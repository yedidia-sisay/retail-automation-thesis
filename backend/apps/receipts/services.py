from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.receipts.models import Receipt, ReceiptLine


def generate_receipt_number(checkout_session: CheckoutSession) -> str:
	date_part = timezone.localdate().strftime("%Y%m%d")
	sequence_part = str(checkout_session.id).zfill(6)
	return f"RCP-{date_part}-{sequence_part}"


def create_receipt_from_checkout(checkout_session: CheckoutSession) -> Receipt:
	with transaction.atomic():
		session = (
			CheckoutSession.objects.select_for_update()
			.select_related("cashier")
			.get(pk=checkout_session.pk)
		)

		if session.status == CheckoutSession.Status.CANCELLED:
			raise ValidationError("Cannot confirm a cancelled checkout session.")

		existing = (
			Receipt.objects.select_related("cashier", "checkout_session")
			.prefetch_related("lines")
			.filter(checkout_session=session)
			.first()
		)
		if existing is not None:
			return existing

		active_items = list(
			CheckoutItem.objects.select_related("product")
			.filter(checkout_session=session, status=CheckoutItem.Status.ACTIVE)
			.order_by("id")
		)
		if not active_items:
			raise ValidationError("Cannot confirm an empty checkout session.")

		total = sum((item.subtotal for item in active_items), Decimal("0.00")).quantize(
			Decimal("0.01")
		)

		now = timezone.now()
		session.subtotal = total
		session.total_amount = total
		session.status = CheckoutSession.Status.CONFIRMED
		if session.confirmed_at is None:
			session.confirmed_at = now
		session.save(
			update_fields=["subtotal", "total_amount", "status", "confirmed_at", "updated_at"]
		)

		receipt = Receipt.objects.create(
			checkout_session=session,
			receipt_number=generate_receipt_number(session),
			cashier=session.cashier,
			total=total,
			payment_status="UNPAID",
		)

		ReceiptLine.objects.bulk_create(
			[
				ReceiptLine(
					receipt=receipt,
					product=item.product,
					product_name=item.product.name,
					product_sku=item.product.sku,
					quantity=item.quantity,
					unit_price=item.unit_price,
					subtotal=item.subtotal,
					source=item.source,
				)
				for item in active_items
			]
		)

		receipt = (
			Receipt.objects.select_related("cashier", "checkout_session")
			.prefetch_related("lines")
			.get(pk=receipt.pk)
		)
		return receipt
