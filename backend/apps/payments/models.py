from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.checkout.models import CheckoutSession
from apps.receipts.models import Receipt


class Payment(models.Model):
	class Method(models.TextChoices):
		CASH = "CASH", "Cash"
		CARD = "CARD", "Card"
		MOBILE_MONEY = "MOBILE_MONEY", "Mobile money"
		BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
		DEMO = "DEMO", "Demo"

	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		COMPLETED = "COMPLETED", "Completed"
		FAILED = "FAILED", "Failed"
		CANCELLED = "CANCELLED", "Cancelled"
		REFUNDED = "REFUNDED", "Refunded"

	receipt = models.ForeignKey(
		Receipt,
		on_delete=models.PROTECT,
		related_name="payments",
	)
	checkout_session = models.ForeignKey(
		CheckoutSession,
		on_delete=models.PROTECT,
		related_name="payments",
		null=True,
		blank=True,
	)
	amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
	method = models.CharField(max_length=20, choices=Method.choices, default=Method.DEMO)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	transaction_reference = models.CharField(
		max_length=100,
		unique=True,
		null=True,
		blank=True,
	)
	provider_name = models.CharField(max_length=100, default="SIMULATED")
	provider_response = models.JSONField(default=dict, blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="payments",
		null=True,
		blank=True,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["receipt", "created_at"]),
			models.Index(fields=["checkout_session", "created_at"]),
			models.Index(fields=["status", "created_at"]),
			models.Index(fields=["method", "created_at"]),
		]

	def __str__(self) -> str:
		ref = self.transaction_reference or "(no-ref)"
		return f"Payment {ref} ({self.status})"
