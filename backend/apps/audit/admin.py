from django.contrib import admin

from apps.audit.models import AuditEvent, ReceiptEvaluation


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
	list_display = (
		"event_type",
		"checkout_session",
		"user",
		"created_at",
	)
	list_select_related = ("checkout_session", "user")
	search_fields = ("event_type", "description", "metadata")
	readonly_fields = (
		"user",
		"checkout_session",
		"event_type",
		"description",
		"metadata",
		"created_at",
	)


@admin.register(ReceiptEvaluation)
class ReceiptEvaluationAdmin(admin.ModelAdmin):
	list_display = (
		"receipt",
		"is_correct",
		"product_names_correct",
		"quantities_correct",
		"prices_correct",
		"total_correct",
		"evaluated_by",
		"created_at",
	)
	list_select_related = ("receipt", "evaluated_by")
	list_filter = ("is_correct", "total_correct", "created_at")
	search_fields = ("receipt__receipt_number", "notes")
