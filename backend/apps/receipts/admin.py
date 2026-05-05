from django.contrib import admin

from apps.receipts.models import Receipt, ReceiptLine


class ReceiptLineInline(admin.TabularInline):
	model = ReceiptLine
	extra = 0
	readonly_fields = (
		"product",
		"product_name",
		"product_sku",
		"quantity",
		"unit_price",
		"subtotal",
		"source",
		"created_at",
	)
	can_delete = False


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
	list_display = (
		"receipt_number",
		"checkout_session",
		"cashier",
		"total",
		"payment_status",
		"created_at",
	)
	list_select_related = ("checkout_session", "cashier")
	search_fields = ("receipt_number", "checkout_session__id", "cashier__username")
	readonly_fields = (
		"receipt_number",
		"checkout_session",
		"cashier",
		"total",
		"payment_status",
		"created_at",
		"updated_at",
	)
	inlines = [ReceiptLineInline]


@admin.register(ReceiptLine)
class ReceiptLineAdmin(admin.ModelAdmin):
	list_display = (
		"receipt",
		"product_sku",
		"product_name",
		"quantity",
		"unit_price",
		"subtotal",
		"source",
		"created_at",
	)
	list_select_related = ("receipt",)
	search_fields = ("receipt__receipt_number", "product_sku", "product_name")
