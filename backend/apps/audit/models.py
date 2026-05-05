from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.checkout.models import CheckoutSession


class AuditEvent(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="audit_events",
		null=True,
		blank=True,
	)
	checkout_session = models.ForeignKey(
		CheckoutSession,
		on_delete=models.SET_NULL,
		related_name="audit_events",
		null=True,
		blank=True,
	)
	event_type = models.CharField(max_length=64)
	description = models.TextField(blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["event_type", "created_at"]),
			models.Index(fields=["checkout_session", "created_at"]),
		]

	def __str__(self) -> str:
		return f"{self.event_type}"
