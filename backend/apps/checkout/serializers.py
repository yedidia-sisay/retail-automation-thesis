from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession


class CheckoutItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    unit_type = serializers.CharField(source="product.unit_type", read_only=True)
    weighted_entry = serializers.SerializerMethodField()

    def get_weighted_entry(self, obj: CheckoutItem):
        # Sprint 7: include weighted entry details when present.
        entry = getattr(obj, "weighted_entry", None)
        if entry is None:
            return None
        from apps.weighted_items.serializers import WeightedItemEntrySerializer

        return WeightedItemEntrySerializer(entry, context=self.context).data

    class Meta:
        model = CheckoutItem
        fields = (
            "id",
            "checkout_session",
            "product",
            "product_name",
            "product_sku",
            "unit_type",
            "quantity",
            "unit_price",
            "subtotal",
            "confidence",
            "source",
            "status",
            "review_status",
            "weighted_entry",
            "note",
            "created_at",
            "updated_at",
        )


class CheckoutSessionSerializer(serializers.ModelSerializer):
    cashier_username = serializers.CharField(source="cashier.username", read_only=True)
    items = CheckoutItemSerializer(many=True, read_only=True)
    receipt_id = serializers.SerializerMethodField()
    receipt_payment_status = serializers.SerializerMethodField()

    def get_receipt_id(self, obj: CheckoutSession):
        receipt = getattr(obj, "receipt", None)
        return getattr(receipt, "id", None)

    def get_receipt_payment_status(self, obj: CheckoutSession):
        receipt = getattr(obj, "receipt", None)
        return getattr(receipt, "payment_status", None)

    class Meta:
        model = CheckoutSession
        fields = (
            "id",
            "cashier",
            "cashier_username",
            "status",
            "subtotal",
            "total_amount",
            "receipt_id",
            "receipt_payment_status",
            "note",
            "items",
            "created_at",
            "updated_at",
            "confirmed_at",
            "cancelled_at",
        )


class CreateCheckoutSessionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class AddManualItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )


class UpdateItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )


class AddBarcodeItemSerializer(serializers.Serializer):
    barcode = serializers.CharField(allow_blank=False)
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
        default=Decimal("1.000"),
    )


class AcceptCheckoutItemSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class RejectCheckoutItemSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class ReplaceCheckoutItemProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
    )
    note = serializers.CharField(required=False, allow_blank=True)


class ChangeCheckoutItemQuantitySerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    note = serializers.CharField(required=False, allow_blank=True)


class CheckoutCorrectionSerializer(serializers.ModelSerializer):
    corrected_by_username = serializers.CharField(
        source="corrected_by.username", read_only=True
    )

    class Meta:
        model = CheckoutCorrection
        fields = (
            "id",
            "checkout_session",
            "checkout_item",
            "correction_type",
            "before_data",
            "after_data",
            "corrected_by",
            "corrected_by_username",
            "note",
            "created_at",
        )
