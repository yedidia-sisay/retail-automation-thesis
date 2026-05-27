from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Product
from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.checkout.services import CheckoutError, ensure_session_is_editable, recalculate_checkout_totals
from apps.weighted_items.models import WeightedItemEntry


_WEIGHT_QUANTITY_QUANT = Decimal("0.001")
_MONEY_QUANT = Decimal("0.01")


def _to_decimal(value) -> Decimal:
	if isinstance(value, Decimal):
		return value
	return Decimal(str(value))


def add_weighted_item_to_checkout(
	checkout_session_id: int,
	product_id: int,
	weight,
	weight_unit: str = WeightedItemEntry.WeightUnit.KG,
	weight_source: str = WeightedItemEntry.WeightSource.MANUAL,
	user=None,
	raw_ocr_text: str | None = None,
) -> WeightedItemEntry:
	"""Add a weighted product to an editable checkout session.

	Sprint 7 note:
	- OCR is NOT implemented. `weight_source=OCR` and `raw_ocr_text` are stored only as placeholders.
	- A numeric `weight` must always be provided.
	"""

	weight_dec = _to_decimal(weight)
	if weight_dec <= 0:
		raise CheckoutError("Weight must be greater than zero.")

	with transaction.atomic():
		session = CheckoutSession.objects.select_for_update().get(pk=checkout_session_id)
		ensure_session_is_editable(session)

		try:
			product = Product.objects.get(pk=product_id, is_active=True)
		except Product.DoesNotExist as exc:
			raise CheckoutError("Product not found or inactive.") from exc

		if product.unit_type not in (Product.UnitType.KG, Product.UnitType.GRAM):
			raise CheckoutError("This product is not sold by weight.")

		# Ensure the cashier-entered unit matches the product pricing unit.
		# Conversions can be added later if needed; Sprint 7 keeps it strict and predictable.
		if weight_unit != product.unit_type:
			raise CheckoutError("Weight unit must match the product unit type.")

		weight_dec = weight_dec.quantize(_WEIGHT_QUANTITY_QUANT)
		unit_price = product.current_price
		subtotal = (weight_dec * unit_price).quantize(_MONEY_QUANT)

		item = CheckoutItem.objects.create(
			checkout_session=session,
			product=product,
			quantity=weight_dec,
			unit_price=unit_price,
			source=CheckoutItem.Source.WEIGHTED,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
		)

		entry = WeightedItemEntry.objects.create(
			checkout_session=session,
			checkout_item=item,
			product=product,
			weight=weight_dec,
			weight_unit=weight_unit,
			unit_price=unit_price,
			subtotal=subtotal,
			weight_source=weight_source,
			raw_ocr_text=(raw_ocr_text or "") if raw_ocr_text is not None else None,
			created_by=user if getattr(user, "is_authenticated", False) else None,
		)

		# Keep CheckoutItem subtotal consistent with our computed subtotal.
		# CheckoutItem.save() recomputes subtotal = quantity * unit_price.
		item.subtotal = subtotal
		item.save(update_fields=["subtotal", "updated_at"])

		recalculate_checkout_totals(session)
		return entry
