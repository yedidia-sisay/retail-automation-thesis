from __future__ import annotations

from decimal import Decimal

from django.db import models, transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.catalog.models import Product
from apps.catalog.selectors import find_product_by_barcode
from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession
from apps.audit.services import log_audit_event


class CheckoutError(Exception):
    pass


def create_checkout_session(cashier=None, note: str = "") -> CheckoutSession:
    with transaction.atomic():
        session = CheckoutSession.objects.create(cashier=cashier, note=note or "")
        return session


def ensure_session_is_editable(session: CheckoutSession) -> None:
    if not session.is_editable:
        raise CheckoutError("This checkout session is not editable.")


def recalculate_checkout_totals(session: CheckoutSession) -> CheckoutSession:
    active_items = (
        CheckoutItem.objects.filter(
            checkout_session=session,
            status__in=[CheckoutItem.Status.ACTIVE, CheckoutItem.Status.NEEDS_REVIEW],
        )
        .exclude(review_status=CheckoutItem.ReviewStatus.REJECTED)
        .only("subtotal")
    )

    subtotal = sum((item.subtotal for item in active_items), Decimal("0.00")).quantize(
        Decimal("0.01")
    )
    session.subtotal = subtotal
    session.total_amount = subtotal
    session.save(update_fields=["subtotal", "total_amount", "updated_at"])
    return session


def add_manual_item(
    session: CheckoutSession, product_id: int, quantity: Decimal
) -> CheckoutItem:
    if quantity is None or quantity <= 0:
        raise CheckoutError("Quantity must be greater than 0.")

    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise CheckoutError("Product not found or inactive.") from exc

        existing_item = (
            CheckoutItem.objects.select_for_update()
            .filter(
                checkout_session=session,
                product=product,
                status=CheckoutItem.Status.ACTIVE,
                source=CheckoutItem.Source.MANUAL,
            )
            .first()
        )

        if existing_item is not None:
            existing_item.quantity = (existing_item.quantity + quantity).quantize(
                Decimal("0.001")
            )
            existing_item.save(update_fields=["quantity", "subtotal", "updated_at"])
            recalculate_checkout_totals(session)
            return existing_item

        item = CheckoutItem.objects.create(
            checkout_session=session,
            product=product,
            quantity=quantity.quantize(Decimal("0.001")),
            unit_price=product.current_price,
            source=CheckoutItem.Source.MANUAL,
            status=CheckoutItem.Status.ACTIVE,
            review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
        )
        recalculate_checkout_totals(session)
        return item


def _serialize_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _checkout_item_snapshot(item: CheckoutItem) -> dict:
    return {
        "id": item.id,
        "checkout_session_id": item.checkout_session_id,
        "product_id": item.product_id,
        "product_name": getattr(item.product, "name", None),
        "product_sku": getattr(item.product, "sku", None),
        "quantity": _serialize_decimal(item.quantity),
        "unit_price": _serialize_decimal(item.unit_price),
        "subtotal": _serialize_decimal(item.subtotal),
        "source": item.source,
        "status": item.status,
        "review_status": item.review_status,
        "confidence": _serialize_decimal(item.confidence),
    }


def _create_correction_log(
    *,
    session: CheckoutSession,
    item: CheckoutItem | None,
    user,
    correction_type: str,
    before_data: dict,
    after_data: dict,
    note: str = "",
) -> CheckoutCorrection:
    return CheckoutCorrection.objects.create(
        checkout_session=session,
        checkout_item=item,
        corrected_by=user,
        correction_type=correction_type,
        before_data=before_data or {},
        after_data=after_data or {},
        note=note or "",
    )


def validate_checkout_can_be_confirmed(session: CheckoutSession) -> None:
    unresolved_items_qs = (
        CheckoutItem.objects.select_related("product")
        .filter(checkout_session=session)
        .exclude(status=CheckoutItem.Status.REMOVED)
        .exclude(review_status=CheckoutItem.ReviewStatus.REJECTED)
        .filter(
            models.Q(review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW)
            | (models.Q(status=CheckoutItem.Status.NEEDS_REVIEW) & ~models.Q(review_status__in=[
                CheckoutItem.ReviewStatus.ACCEPTED,
                CheckoutItem.ReviewStatus.REPLACED,
            ]))
        )
    )

    if unresolved_items_qs.exists():
        unresolved_items = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "source": item.source,
                "status": item.status,
                "review_status": item.review_status,
                "confidence": _serialize_decimal(item.confidence),
            }
            for item in unresolved_items_qs.order_by("id")
        ]
        raise ValidationError(
            {
                "detail": "Checkout cannot be confirmed. Some detected items still need review by the cashier.",
                "unresolved_items": unresolved_items,
            }
        )

    has_countable_items = CheckoutItem.objects.filter(
        checkout_session=session,
        status__in=[CheckoutItem.Status.ACTIVE, CheckoutItem.Status.NEEDS_REVIEW],
    ).exclude(
        status=CheckoutItem.Status.REMOVED
    ).exclude(
        review_status=CheckoutItem.ReviewStatus.REJECTED
    ).exists()
    if not has_countable_items:
        raise ValidationError({"detail": "Cannot confirm an empty checkout session."})


def update_item_quantity(
    item: CheckoutItem, quantity: Decimal, user=None, note: str = ""
) -> CheckoutItem:
    if quantity is None or quantity <= 0:
        raise CheckoutError("Quantity must be greater than 0.")

    with transaction.atomic():
        item = CheckoutItem.objects.select_for_update().select_related(
            "checkout_session", "product"
        ).get(pk=item.pk)
        session = item.checkout_session
        ensure_session_is_editable(session)

        before = _checkout_item_snapshot(item)

        item.quantity = quantity.quantize(Decimal("0.001"))
        # If cashier explicitly changes quantity, treat it as reviewed.
        if item.review_status == CheckoutItem.ReviewStatus.NEEDS_REVIEW:
            item.review_status = CheckoutItem.ReviewStatus.ACCEPTED
        if item.status == CheckoutItem.Status.NEEDS_REVIEW:
            item.status = CheckoutItem.Status.ACTIVE

        item.save(update_fields=["quantity", "subtotal", "status", "review_status", "updated_at"])

        after = _checkout_item_snapshot(item)
        _create_correction_log(
            session=session,
            item=item,
            user=user,
            correction_type=CheckoutCorrection.CorrectionType.CHANGE_QUANTITY,
            before_data=before,
            after_data=after,
            note=note,
        )
        recalculate_checkout_totals(session)
        return item


def remove_item(item: CheckoutItem) -> CheckoutItem:
    with transaction.atomic():
        item = CheckoutItem.objects.select_for_update().select_related(
            "checkout_session"
        ).get(pk=item.pk)
        session = item.checkout_session
        ensure_session_is_editable(session)

        if item.status != CheckoutItem.Status.REMOVED:
            item.status = CheckoutItem.Status.REMOVED
            item.save(update_fields=["status", "updated_at"])

        recalculate_checkout_totals(session)
        return item


def accept_checkout_item(item_id: int, user=None, note: str = "") -> CheckoutItem:
    with transaction.atomic():
        item = (
            CheckoutItem.objects.select_for_update()
            .select_related("checkout_session", "product")
            .get(pk=item_id)
        )
        session = item.checkout_session
        ensure_session_is_editable(session)

        before = _checkout_item_snapshot(item)

        if item.status == CheckoutItem.Status.REMOVED:
            raise CheckoutError("Cannot accept a removed item.")

        item.review_status = CheckoutItem.ReviewStatus.ACCEPTED
        if item.status == CheckoutItem.Status.NEEDS_REVIEW:
            item.status = CheckoutItem.Status.ACTIVE
        item.save(update_fields=["review_status", "status", "updated_at"])

        after = _checkout_item_snapshot(item)
        _create_correction_log(
            session=session,
            item=item,
            user=user,
            correction_type=CheckoutCorrection.CorrectionType.ACCEPT_ITEM,
            before_data=before,
            after_data=after,
            note=note,
        )

        recalculate_checkout_totals(session)
        return item


def reject_checkout_item(item_id: int, user=None, note: str = "") -> CheckoutItem:
    with transaction.atomic():
        item = (
            CheckoutItem.objects.select_for_update()
            .select_related("checkout_session", "product")
            .get(pk=item_id)
        )
        session = item.checkout_session
        ensure_session_is_editable(session)

        before = _checkout_item_snapshot(item)

        item.review_status = CheckoutItem.ReviewStatus.REJECTED
        item.status = CheckoutItem.Status.REMOVED
        item.save(update_fields=["review_status", "status", "updated_at"])

        after = _checkout_item_snapshot(item)
        _create_correction_log(
            session=session,
            item=item,
            user=user,
            correction_type=CheckoutCorrection.CorrectionType.REJECT_ITEM,
            before_data=before,
            after_data=after,
            note=note,
        )

        recalculate_checkout_totals(session)
        return item


def replace_checkout_item_product(
    item_id: int,
    product_id: int,
    quantity: Decimal | None = None,
    user=None,
    note: str = "",
) -> CheckoutItem:
    with transaction.atomic():
        item = (
            CheckoutItem.objects.select_for_update()
            .select_related("checkout_session", "product")
            .get(pk=item_id)
        )
        session = item.checkout_session
        ensure_session_is_editable(session)

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise CheckoutError("Product not found or inactive.") from exc

        before = _checkout_item_snapshot(item)

        item.product = product
        item.unit_price = product.current_price
        if quantity is not None:
            if quantity <= 0:
                raise CheckoutError("Quantity must be greater than 0.")
            item.quantity = quantity.quantize(Decimal("0.001"))

        item.status = CheckoutItem.Status.ACTIVE
        item.review_status = CheckoutItem.ReviewStatus.REPLACED
        item.save(
            update_fields=[
                "product",
                "unit_price",
                "quantity",
                "subtotal",
                "status",
                "review_status",
                "updated_at",
            ]
        )

        after = _checkout_item_snapshot(item)
        _create_correction_log(
            session=session,
            item=item,
            user=user,
            correction_type=CheckoutCorrection.CorrectionType.REPLACE_PRODUCT,
            before_data=before,
            after_data=after,
            note=note,
        )

        recalculate_checkout_totals(session)
        return item


def change_checkout_item_quantity(
    item_id: int, quantity: Decimal, user=None, note: str = ""
) -> CheckoutItem:
    item = CheckoutItem.objects.get(pk=item_id)
    return update_item_quantity(item=item, quantity=quantity, user=user, note=note)


def confirm_checkout_session(session: CheckoutSession) -> CheckoutSession:
    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)

        validate_checkout_can_be_confirmed(session)

        recalculate_checkout_totals(session)
        session.confirm()
        return session


def cancel_checkout_session(session: CheckoutSession) -> CheckoutSession:
    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)

        session.cancel()
        return session


def add_barcode_item_to_checkout(
    session: CheckoutSession,
    barcode: str,
    quantity: Decimal | None = None,
    user=None,
) -> CheckoutSession:
    barcode_value = (barcode or "").strip()
    if not barcode_value:
        raise ValidationError("Barcode cannot be blank.")

    product = find_product_by_barcode(barcode_value)

    if quantity is None:
        quantity = Decimal("1.000")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0.")

    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)
        if product is None:
            # Log outside this transaction so it isn't rolled back.
            pass
        else:
            existing_item = (
                CheckoutItem.objects.select_for_update()
                .filter(
                    checkout_session=session,
                    product=product,
                    status=CheckoutItem.Status.ACTIVE,
                    source=CheckoutItem.Source.BARCODE,
                )
                .first()
            )

            quantity = quantity.quantize(Decimal("0.001"))
            if existing_item is not None:
                existing_item.quantity = (existing_item.quantity + quantity).quantize(
                    Decimal("0.001")
                )
                existing_item.save(update_fields=["quantity", "subtotal", "updated_at"])
            else:
                CheckoutItem.objects.create(
                    checkout_session=session,
                    product=product,
                    quantity=quantity,
                    unit_price=product.current_price,
                    source=CheckoutItem.Source.BARCODE,
                    status=CheckoutItem.Status.ACTIVE,
                    review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
                )

            recalculate_checkout_totals(session)

    if product is None:
        log_audit_event(
            user=user,
            checkout_session=session,
            event_type="BARCODE_FALLBACK_UNKNOWN",
            description="Unknown barcode scanned during checkout.",
            metadata={"barcode": barcode_value},
        )
        raise NotFound("No active product found for this barcode.")

    log_audit_event(
        user=user,
        checkout_session=session,
        event_type="BARCODE_FALLBACK_SUCCESS",
        description="Product added using barcode fallback.",
        metadata={
            "barcode": barcode_value,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": str(quantity.quantize(Decimal("0.001"))),
        },
    )

    return session


def add_detection_results_to_checkout(
    session: CheckoutSession,
    detection_run,
) -> list[CheckoutItem]:
    """Convert eligible DetectedObject rows into grouped VISION checkout items.

    - Only AUTO_ACCEPTED / NEEDS_REVIEW detections with a matched product are turned into items.
    - Duplicate products are grouped into a single quantity.
    - Items marked NEEDS_REVIEW prevent checkout confirmation.
    """

    from decimal import Decimal as D

    from apps.vision.models import DetectedObject

    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)

        objects = list(
            DetectedObject.objects.select_related("matched_product")
            .filter(detection_run=detection_run)
            .only("matched_product", "review_status", "confidence")
        )

        eligible_statuses = {
            DetectedObject.ReviewStatus.AUTO_ACCEPTED,
            DetectedObject.ReviewStatus.NEEDS_REVIEW,
        }

        grouped: dict[int, dict] = {}
        for obj in objects:
            if obj.matched_product_id is None:
                continue
            if obj.review_status not in eligible_statuses:
                continue

            entry = grouped.get(obj.matched_product_id)
            if entry is None:
                entry = {
                    "product": obj.matched_product,
                    "count": 0,
                    "any_needs_review": False,
                    "conf_sum": D("0"),
                }
                grouped[obj.matched_product_id] = entry

            entry["count"] += 1
            if obj.review_status == DetectedObject.ReviewStatus.NEEDS_REVIEW:
                entry["any_needs_review"] = True
            entry["conf_sum"] += D(str(obj.confidence))

        created_or_updated: list[CheckoutItem] = []
        for product_id, entry in grouped.items():
            product: Product = entry["product"]
            count: int = entry["count"]
            any_needs_review: bool = entry["any_needs_review"]
            conf_sum: D = entry["conf_sum"]

            quantity = D(count).quantize(D("0.001"))
            new_status = (
                CheckoutItem.Status.NEEDS_REVIEW if any_needs_review else CheckoutItem.Status.ACTIVE
            )
            new_review_status = (
                CheckoutItem.ReviewStatus.NEEDS_REVIEW
                if any_needs_review
                else CheckoutItem.ReviewStatus.NOT_REQUIRED
            )
            avg_conf = (conf_sum / D(count)).quantize(D("0.0001")) if count else None

            existing_item = (
                CheckoutItem.objects.select_for_update()
                .filter(
                    checkout_session=session,
                    product_id=product_id,
                    status__in=[CheckoutItem.Status.ACTIVE, CheckoutItem.Status.NEEDS_REVIEW],
                    source=CheckoutItem.Source.VISION,
                )
                .first()
            )

            if existing_item is not None:
                existing_item.quantity = (existing_item.quantity + quantity).quantize(D("0.001"))
                if (
                    existing_item.status == CheckoutItem.Status.NEEDS_REVIEW
                    or new_status == CheckoutItem.Status.NEEDS_REVIEW
                ):
                    existing_item.status = CheckoutItem.Status.NEEDS_REVIEW
                if (
                    existing_item.review_status == CheckoutItem.ReviewStatus.NEEDS_REVIEW
                    or new_review_status == CheckoutItem.ReviewStatus.NEEDS_REVIEW
                ):
                    existing_item.review_status = CheckoutItem.ReviewStatus.NEEDS_REVIEW
                existing_item.unit_price = product.current_price
                if avg_conf is not None:
                    if existing_item.confidence is None:
                        existing_item.confidence = avg_conf
                    else:
                        existing_item.confidence = min(existing_item.confidence, avg_conf)

                existing_item.save(
                    update_fields=[
                        "quantity",
                        "unit_price",
                        "subtotal",
                        "status",
                        "review_status",
                        "confidence",
                        "updated_at",
                    ]
                )
                created_or_updated.append(existing_item)
                continue

            item = CheckoutItem.objects.create(
                checkout_session=session,
                product=product,
                quantity=quantity,
                unit_price=product.current_price,
                source=CheckoutItem.Source.VISION,
                status=new_status,
                review_status=new_review_status,
                confidence=avg_conf,
                note=f"DetectionRun #{getattr(detection_run, 'id', '')}",
            )
            created_or_updated.append(item)

        recalculate_checkout_totals(session)
        return created_or_updated
