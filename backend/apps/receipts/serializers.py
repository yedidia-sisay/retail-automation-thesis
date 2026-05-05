from __future__ import annotations

from rest_framework import serializers

from apps.receipts.models import Receipt, ReceiptLine


class ReceiptLineSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReceiptLine
		fields = (
			"id",
			"product",
			"product_name",
			"product_sku",
			"quantity",
			"unit_price",
			"subtotal",
			"source",
			"created_at",
		)
		read_only_fields = fields


class ReceiptSerializer(serializers.ModelSerializer):
	lines = ReceiptLineSerializer(many=True, read_only=True)

	class Meta:
		model = Receipt
		fields = (
			"id",
			"receipt_number",
			"checkout_session",
			"cashier",
			"total",
			"payment_status",
			"created_at",
			"lines",
		)
		read_only_fields = fields
