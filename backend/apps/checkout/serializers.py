from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.checkout.models import CheckoutItem, CheckoutSession


class CheckoutItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    unit_type = serializers.CharField(source="product.unit_type", read_only=True)

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
            "source",
            "status",
            "note",
            "created_at",
            "updated_at",
        )


class CheckoutSessionSerializer(serializers.ModelSerializer):
    cashier_username = serializers.CharField(source="cashier.username", read_only=True)
    items = CheckoutItemSerializer(many=True, read_only=True)

    class Meta:
        model = CheckoutSession
        fields = (
            "id",
            "cashier",
            "cashier_username",
            "status",
            "subtotal",
            "total_amount",
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
