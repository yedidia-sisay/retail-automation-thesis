from __future__ import annotations

from decimal import Decimal

from apps.catalog.models import DetectionClassMapping, Product, ProductBarcode


def find_product_by_barcode(barcode: str | None) -> Product | None:
	barcode_value = (barcode or "").strip()
	if not barcode_value:
		return None

	# Prefer the ProductBarcode table.
	barcode_obj = (
		ProductBarcode.objects.select_related("product")
		.filter(barcode=barcode_value, product__is_active=True)
		.only("product")
		.first()
	)
	if barcode_obj is not None:
		return barcode_obj.product

	# Fallback if Product has a direct barcode field (not currently used in this codebase).
	if hasattr(Product, "barcode"):
		try:
			product = Product.objects.filter(barcode=barcode_value, is_active=True).first()
		except Exception:
			return None
		return product

	return None


def get_product_for_detection_class(class_name: str) -> tuple[Product, Decimal] | None:
	class_name_value = (class_name or "").strip()
	if not class_name_value:
		return None

	mapping = (
		DetectionClassMapping.objects.select_related("product")
		.filter(
			class_name=class_name_value,
			is_active=True,
			product__is_active=True,
		)
		.only("product", "minimum_confidence")
		.first()
	)
	if mapping is None:
		return None

	return (mapping.product, mapping.minimum_confidence)
