from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.catalog.models import Product
from apps.weighted_items.models import WeightedItemEntry


class AddWeightedItemSerializer(serializers.Serializer):
	product_id = serializers.IntegerField()
	weight = serializers.DecimalField(max_digits=10, decimal_places=3)
	weight_unit = serializers.ChoiceField(
		choices=WeightedItemEntry.WeightUnit.choices,
		required=False,
		default=WeightedItemEntry.WeightUnit.KG,
	)
	weight_source = serializers.ChoiceField(
		choices=WeightedItemEntry.WeightSource.choices,
		required=False,
		default=WeightedItemEntry.WeightSource.MANUAL,
	)
	raw_ocr_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)

	def validate_weight(self, value: Decimal) -> Decimal:
		if value is None or value <= 0:
			raise serializers.ValidationError("Weight must be greater than zero.")
		return value

	def validate(self, attrs: dict) -> dict:
		product_id = attrs.get("product_id")
		weight_unit = attrs.get("weight_unit")

		try:
			product = Product.objects.get(pk=product_id)
		except Product.DoesNotExist as exc:
			raise serializers.ValidationError({"detail": "Invalid product."}) from exc

		if not product.is_active:
			raise serializers.ValidationError({"detail": "Product not found or inactive."})

		if product.unit_type not in (Product.UnitType.KG, Product.UnitType.GRAM):
			raise serializers.ValidationError({"detail": "This product is not sold by weight."})

		if weight_unit != product.unit_type:
			raise serializers.ValidationError(
				{"detail": "Weight unit must match the product unit type."}
			)

		return attrs


class WeightedItemEntrySerializer(serializers.ModelSerializer):
	product_name = serializers.CharField(source="product.name", read_only=True)

	class Meta:
		model = WeightedItemEntry
		fields = (
			"id",
			"checkout_session",
			"checkout_item",
			"product",
			"product_name",
			"weight",
			"weight_unit",
			"unit_price",
			"subtotal",
			"weight_source",
			"raw_ocr_text",
			"created_at",
		)
		read_only_fields = fields
