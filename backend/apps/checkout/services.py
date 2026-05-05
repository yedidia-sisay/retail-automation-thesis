from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.catalog.models import Product
from apps.catalog.selectors import find_product_by_barcode
from apps.checkout.models import CheckoutItem, CheckoutSession
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
    active_items = CheckoutItem.objects.filter(
        checkout_session=session,
        status=CheckoutItem.Status.ACTIVE,
    ).only("subtotal")

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
        )
        recalculate_checkout_totals(session)
        return item


def update_item_quantity(item: CheckoutItem, quantity: Decimal) -> CheckoutItem:
    if quantity is None or quantity <= 0:
        raise CheckoutError("Quantity must be greater than 0.")

    with transaction.atomic():
        item = CheckoutItem.objects.select_for_update().select_related(
            "checkout_session"
        ).get(pk=item.pk)
        session = item.checkout_session
        ensure_session_is_editable(session)

        item.quantity = quantity.quantize(Decimal("0.001"))
        item.save(update_fields=["quantity", "subtotal", "updated_at"])
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


def confirm_checkout_session(session: CheckoutSession) -> CheckoutSession:
    with transaction.atomic():
        session = CheckoutSession.objects.select_for_update().get(pk=session.pk)
        ensure_session_is_editable(session)

        has_active_items = CheckoutItem.objects.filter(
            checkout_session=session,
            status=CheckoutItem.Status.ACTIVE,
        ).exists()
        if not has_active_items:
            raise CheckoutError("Cannot confirm an empty checkout session.")

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
