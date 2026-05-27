from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"receipt",
		"checkout_session",
		"amount",
		"method",
		"status",
		"transaction_reference",
		"provider_name",
		"created_at",
	)
	list_filter = ("status", "method", "provider_name", "created_at")
	search_fields = (
		"transaction_reference",
		"receipt__id",
		"checkout_session__id",
	)
	ordering = ("-created_at",)
