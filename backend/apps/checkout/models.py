from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import Product


class CheckoutSession(models.Model):
	class Status(models.TextChoices):
		OPEN = "OPEN", "Open"
		CONFIRMED = "CONFIRMED", "Confirmed"
		CANCELLED = "CANCELLED", "Cancelled"

	cashier = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="checkout_sessions",
		null=True,
		blank=True,
	)
	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.OPEN,
	)
	subtotal = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
	)
	total_amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		default=Decimal("0.00"),
	)
	confirmed_at = models.DateTimeField(null=True, blank=True)
	cancelled_at = models.DateTimeField(null=True, blank=True)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["status", "created_at"]),
			models.Index(fields=["cashier", "created_at"]),
		]

	def __str__(self) -> str:
		return f"CheckoutSession #{self.pk} ({self.status})"

	@property
	def is_editable(self) -> bool:
		return self.status == self.Status.OPEN

	def confirm(self) -> None:
		self.status = self.Status.CONFIRMED
		self.confirmed_at = timezone.now()
		self.save(update_fields=["status", "confirmed_at", "updated_at"])

	def cancel(self) -> None:
		self.status = self.Status.CANCELLED
		self.cancelled_at = timezone.now()
		self.save(update_fields=["status", "cancelled_at", "updated_at"])


class CheckoutItem(models.Model):
	class Source(models.TextChoices):
		MANUAL = "MANUAL", "Manual"
		VISION = "VISION", "Vision"
		BARCODE = "BARCODE", "Barcode"
		WEIGHTED = "WEIGHTED", "Weighted"

	class Status(models.TextChoices):
		ACTIVE = "ACTIVE", "Active"
		REMOVED = "REMOVED", "Removed"

	checkout_session = models.ForeignKey(
		CheckoutSession,
		on_delete=models.CASCADE,
		related_name="items",
	)
	product = models.ForeignKey(
		Product,
		on_delete=models.PROTECT,
		related_name="checkout_items",
	)
	quantity = models.DecimalField(
		max_digits=10,
		decimal_places=3,
		default=Decimal("1.000"),
	)
	unit_price = models.DecimalField(max_digits=12, decimal_places=2)
	subtotal = models.DecimalField(max_digits=12, decimal_places=2)
	source = models.CharField(
		max_length=20,
		choices=Source.choices,
		default=Source.MANUAL,
	)
	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.ACTIVE,
	)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("created_at",)
		indexes = [
			models.Index(fields=["checkout_session", "status"]),
			models.Index(fields=["product"]),
			models.Index(fields=["source"]),
		]

	def __str__(self) -> str:
		return f"Item #{self.pk} {self.product.sku} x {self.quantity}"

	def calculate_subtotal(self) -> Decimal:
		return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

	def save(self, *args, **kwargs):
		self.subtotal = self.calculate_subtotal()
		return super().save(*args, **kwargs)
