from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Product
from apps.checkout.models import CheckoutItem, CheckoutSession


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
