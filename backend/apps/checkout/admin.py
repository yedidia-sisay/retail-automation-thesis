from django.contrib import admin

from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession


class CheckoutItemInline(admin.TabularInline):
	model = CheckoutItem
	extra = 0
	fields = (
		"product",
		"quantity",
		"unit_price",
		"subtotal",
		"confidence",
		"source",
		"status",
		"review_status",
		"note",
		"created_at",
	)
	readonly_fields = ("subtotal", "created_at")


@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"cashier",
		"status",
		"subtotal",
		"total_amount",
		"created_at",
		"confirmed_at",
		"cancelled_at",
	)
	list_filter = ("status", "created_at")
	search_fields = ("=id", "cashier__username")
	readonly_fields = (
		"subtotal",
		"total_amount",
		"created_at",
		"updated_at",
		"confirmed_at",
		"cancelled_at",
	)
	inlines = [CheckoutItemInline]


@admin.register(CheckoutItem)
class CheckoutItemAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"checkout_session",
		"product",
		"quantity",
		"unit_price",
		"subtotal",
		"confidence",
		"source",
		"status",
		"review_status",
		"created_at",
	)
	list_filter = ("source", "status", "review_status", "created_at")
	search_fields = ("product__name", "product__sku", "=checkout_session__id")
	readonly_fields = ("subtotal", "created_at", "updated_at")


@admin.register(CheckoutCorrection)
class CheckoutCorrectionAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"checkout_session",
		"checkout_item",
		"correction_type",
		"corrected_by",
		"created_at",
	)
	list_filter = ("correction_type", "created_at")
	search_fields = ("=checkout_session__id", "=checkout_item__id", "corrected_by__username")
	readonly_fields = (
		"checkout_session",
		"checkout_item",
		"corrected_by",
		"correction_type",
		"before_data",
		"after_data",
		"note",
		"created_at",
	)
