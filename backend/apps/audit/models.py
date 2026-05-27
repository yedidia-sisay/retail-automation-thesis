from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.checkout.models import CheckoutSession
from apps.receipts.models import Receipt


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


class ReceiptEvaluation(models.Model):
	receipt = models.OneToOneField(
		Receipt,
		on_delete=models.CASCADE,
		related_name="evaluation",
	)
	evaluated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="receipt_evaluations",
		null=True,
		blank=True,
	)
	is_correct = models.BooleanField()
	product_names_correct = models.BooleanField(default=True)
	quantities_correct = models.BooleanField(default=True)
	prices_correct = models.BooleanField(default=True)
	subtotals_correct = models.BooleanField(default=True)
	total_correct = models.BooleanField(default=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["is_correct", "created_at"]),
			models.Index(fields=["total_correct", "created_at"]),
		]

	def __str__(self) -> str:
		return f"ReceiptEvaluation #{self.pk} for {self.receipt_id}"
