from __future__ import annotations

from apps.catalog.models import Product, ProductBarcode


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
