from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.catalog.models import Product
from apps.checkout.models import CheckoutSession


class Receipt(models.Model):
	checkout_session = models.OneToOneField(
		CheckoutSession,
		on_delete=models.PROTECT,
		related_name="receipt",
	)
	receipt_number = models.CharField(max_length=64, unique=True)
	cashier = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="receipts",
		null=True,
		blank=True,
	)
	total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	payment_status = models.CharField(max_length=20, default="UNPAID")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["receipt_number"]),
			models.Index(fields=["created_at"]),
		]

	def __str__(self) -> str:
		return f"{self.receipt_number}"


class ReceiptLine(models.Model):
	receipt = models.ForeignKey(
		Receipt,
		on_delete=models.CASCADE,
		related_name="lines",
	)
	product = models.ForeignKey(
		Product,
		on_delete=models.SET_NULL,
		related_name="receipt_lines",
		null=True,
		blank=True,
	)
	product_name = models.CharField(max_length=255)
	product_sku = models.CharField(max_length=64, blank=True)
	quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1.000"))
	unit_price = models.DecimalField(max_digits=12, decimal_places=2)
	subtotal = models.DecimalField(max_digits=12, decimal_places=2)
	source = models.CharField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("created_at",)
		indexes = [
			models.Index(fields=["receipt"]),
			models.Index(fields=["product_sku"]),
		]

	def __str__(self) -> str:
		return f"{self.product_sku} x {self.quantity}"
