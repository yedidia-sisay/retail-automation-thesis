from django.contrib import admin

from apps.erp.models import ERPProductMapping, ERPReceiptMapping, ERPSyncLog


@admin.register(ERPSyncLog)
class ERPSyncLogAdmin(admin.ModelAdmin):
	list_display = (
		"object_type",
		"object_id",
		"action",
		"status",
		"erp_system",
		"created_at",
	)
	list_filter = (
		"object_type",
		"action",
		"status",
		"erp_system",
		"created_at",
	)
	search_fields = ("object_id", "error_message")
	readonly_fields = ("created_at",)


@admin.register(ERPProductMapping)
class ERPProductMappingAdmin(admin.ModelAdmin):
	list_display = (
		"product",
		"erp_system",
		"erp_product_id",
		"erp_product_name",
		"is_active",
		"last_synced_at",
	)
	list_filter = ("erp_system", "is_active")
	search_fields = ("product__sku", "product__name", "erp_product_id", "erp_product_name")


@admin.register(ERPReceiptMapping)
class ERPReceiptMappingAdmin(admin.ModelAdmin):
	list_display = (
		"receipt",
		"erp_system",
		"erp_reference",
		"sync_status",
		"synced_at",
		"created_at",
	)
	list_filter = ("erp_system", "sync_status", "created_at")
	search_fields = ("receipt__receipt_number", "erp_reference", "error_message")
