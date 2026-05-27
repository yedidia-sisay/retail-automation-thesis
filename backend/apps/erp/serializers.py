from __future__ import annotations

from rest_framework import serializers

from apps.erp.models import ERPProductMapping, ERPReceiptMapping, ERPSyncLog


class ERPSyncLogSerializer(serializers.ModelSerializer):
	class Meta:
		model = ERPSyncLog
		fields = (
			"id",
			"object_type",
			"object_id",
			"action",
			"status",
			"erp_system",
			"request_payload",
			"response_payload",
			"error_message",
			"created_at",
		)
		read_only_fields = fields


class ERPReceiptMappingSerializer(serializers.ModelSerializer):
	class Meta:
		model = ERPReceiptMapping
		fields = (
			"id",
			"receipt",
			"erp_system",
			"erp_receipt_id",
			"erp_reference",
			"sync_status",
			"error_message",
			"synced_at",
			"created_at",
		)
		read_only_fields = fields


class ERPProductMappingSerializer(serializers.ModelSerializer):
	product_name = serializers.CharField(source="product.name", read_only=True)

	class Meta:
		model = ERPProductMapping
		fields = (
			"id",
			"product",
			"product_name",
			"erp_system",
			"erp_product_id",
			"erp_product_name",
			"last_synced_at",
			"is_active",
		)
		read_only_fields = fields


class PushReceiptERPSerializer(serializers.Serializer):
	receipt_id = serializers.IntegerField()


class SyncProductsSerializer(serializers.Serializer):
	create_missing = serializers.BooleanField(required=False, default=False)
