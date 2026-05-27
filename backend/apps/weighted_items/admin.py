from django.contrib import admin

from apps.weighted_items.models import WeightedItemEntry


@admin.register(WeightedItemEntry)
class WeightedItemEntryAdmin(admin.ModelAdmin):
	list_display = (
		"checkout_session",
		"product",
		"weight",
		"weight_unit",
		"unit_price",
		"subtotal",
		"weight_source",
		"created_at",
	)
	list_filter = ("weight_source", "weight_unit", "created_at")
	search_fields = (
		"product__name",
		"product__sku",
		"checkout_session__id",
	)
	raw_id_fields = ("checkout_session", "checkout_item", "product", "created_by")
