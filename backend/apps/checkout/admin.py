from django.contrib import admin

from apps.checkout.models import CheckoutItem, CheckoutSession


class CheckoutItemInline(admin.TabularInline):
	model = CheckoutItem
	extra = 0
	fields = (
		"product",
		"quantity",
		"unit_price",
		"subtotal",
		"source",
		"status",
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
		"source",
		"status",
		"created_at",
	)
	list_filter = ("source", "status", "created_at")
	search_fields = ("product__name", "product__sku", "=checkout_session__id")
	readonly_fields = ("subtotal", "created_at", "updated_at")
