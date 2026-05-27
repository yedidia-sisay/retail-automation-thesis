from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.catalog.models import Product
from apps.checkout.models import CheckoutItem, CheckoutSession


class WeightedItemEntry(models.Model):
	class WeightUnit(models.TextChoices):
		KG = "KG", "Kilogram"
		GRAM = "GRAM", "Gram"

	class WeightSource(models.TextChoices):
		MANUAL = "MANUAL", "Manual"
		OCR = "OCR", "OCR"

	checkout_session = models.ForeignKey(
		CheckoutSession,
		on_delete=models.CASCADE,
		related_name="weighted_entries",
	)
	checkout_item = models.OneToOneField(
		CheckoutItem,
		on_delete=models.SET_NULL,
		related_name="weighted_entry",
		null=True,
		blank=True,
	)
	product = models.ForeignKey(
		Product,
		on_delete=models.PROTECT,
		related_name="weighted_entries",
	)
	weight = models.DecimalField(max_digits=10, decimal_places=3)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
	weight_unit = models.CharField(
		max_length=10,
		choices=WeightUnit.choices,
		default=WeightUnit.KG,
	)
	weight_source = models.CharField(
		max_length=10,
		choices=WeightSource.choices,
		default=WeightSource.MANUAL,
	)
	raw_ocr_text = models.CharField(max_length=255, blank=True, null=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="weighted_item_entries",
		null=True,
		blank=True,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["checkout_session", "created_at"]),
			models.Index(fields=["product", "created_at"]),
			models.Index(fields=["weight_source", "created_at"]),
		]

	def __str__(self) -> str:
		return f"WeightedEntry #{self.pk} {self.product.sku} {self.weight} {self.weight_unit}"
