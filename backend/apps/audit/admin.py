from django.contrib import admin

from apps.audit.models import AuditEvent


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
