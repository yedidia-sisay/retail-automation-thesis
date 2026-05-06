from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.payments.models import Payment
from apps.receipts.models import Receipt


class SimulatePaymentSerializer(serializers.Serializer):
	receipt_id = serializers.IntegerField()
	method = serializers.ChoiceField(
		choices=Payment.Method.values,
		required=False,
		default=Payment.Method.DEMO,
	)
	status = serializers.ChoiceField(
		choices=[
			Payment.Status.PENDING,
			Payment.Status.COMPLETED,
			Payment.Status.FAILED,
			Payment.Status.CANCELLED,
		],
		required=False,
		default=Payment.Status.COMPLETED,
	)
	amount = serializers.DecimalField(
		max_digits=10,
		decimal_places=2,
		required=False,
		allow_null=True,
	)
	provider_response = serializers.JSONField(required=False)

	def validate_amount(self, value: Decimal | None) -> Decimal | None:
		if value is None:
			return None
		if value <= 0:
			raise serializers.ValidationError("Amount must be greater than zero.")
		return value.quantize(Decimal("0.01"))

	def validate(self, attrs: dict) -> dict:
		receipt_id = attrs.get("receipt_id")
		amount = attrs.get("amount")

		try:
			receipt = Receipt.objects.only("id", "total").get(pk=receipt_id)
		except Receipt.DoesNotExist:
			raise serializers.ValidationError({"detail": "Receipt not found."})

		receipt_total = (receipt.total or Decimal("0.00")).quantize(Decimal("0.01"))
		if amount is not None and amount != receipt_total:
			raise serializers.ValidationError({"detail": "Payment amount must match receipt total."})

		return attrs


class PaymentSerializer(serializers.ModelSerializer):
	receipt = serializers.IntegerField(source="receipt_id", read_only=True)
	checkout_session = serializers.IntegerField(source="checkout_session_id", read_only=True)
	created_by = serializers.IntegerField(source="created_by_id", read_only=True)

	class Meta:
		model = Payment
		fields = (
			"id",
			"receipt",
			"checkout_session",
			"amount",
			"method",
			"status",
			"transaction_reference",
			"provider_name",
			"provider_response",
			"created_by",
			"created_at",
		)
		read_only_fields = fields
