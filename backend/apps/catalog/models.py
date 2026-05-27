from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
	name = models.CharField(max_length=255)
	slug = models.SlugField(max_length=255, unique=True)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("name",)

	def __str__(self) -> str:
		return self.name


class Product(models.Model):
	class UnitType(models.TextChoices):
		PIECE = "PIECE", "Piece"
		KG = "KG", "Kilogram"
		GRAM = "GRAM", "Gram"

	class SyncStatus(models.TextChoices):
		LOCAL_ONLY = "LOCAL_ONLY", "Local only"
		SYNCED = "SYNCED", "Synced"
		NEEDS_SYNC = "NEEDS_SYNC", "Needs sync"
		SYNC_FAILED = "SYNC_FAILED", "Sync failed"

	category = models.ForeignKey(
		Category,
		on_delete=models.PROTECT,
		related_name="products",
	)
	name = models.CharField(max_length=255)
	sku = models.CharField(max_length=64, unique=True)
	unit_type = models.CharField(max_length=10, choices=UnitType.choices)
	current_price = models.DecimalField(max_digits=10, decimal_places=2)
	description = models.TextField(blank=True)
	image = models.ImageField(upload_to="catalog/products/", blank=True, null=True)
	is_active = models.BooleanField(default=True)
	odoo_product_id = models.CharField(max_length=128, blank=True, null=True)
	last_synced_at = models.DateTimeField(blank=True, null=True)
	sync_status = models.CharField(
		max_length=20,
		choices=SyncStatus.choices,
		default=SyncStatus.LOCAL_ONLY,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("name",)
		indexes = [
			models.Index(fields=["sku"]),
			models.Index(fields=["name"]),
			models.Index(fields=["is_active"]),
			models.Index(fields=["odoo_product_id"]),
		]

	def __str__(self) -> str:
		return f"{self.name} ({self.sku})"


class ProductBarcode(models.Model):
	product = models.ForeignKey(
		Product,
		on_delete=models.CASCADE,
		related_name="barcodes",
	)
	barcode = models.CharField(max_length=64, unique=True)
	is_primary = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("product", "-is_primary", "barcode")
		constraints = [
			models.UniqueConstraint(
				fields=["product"],
				condition=models.Q(is_primary=True),
				name="unique_primary_barcode_per_product",
			)
		]
		indexes = [models.Index(fields=["barcode"])]

	def __str__(self) -> str:
		return f"{self.barcode} → {self.product.sku}"


class DetectionClassMapping(models.Model):
	class_name = models.CharField(max_length=255, unique=True)
	product = models.ForeignKey(
		Product,
		on_delete=models.PROTECT,
		related_name="detection_mappings",
	)
	minimum_confidence = models.DecimalField(
		max_digits=4,
		decimal_places=2,
		default=Decimal("0.70"),
		validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
	)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("class_name",)
		indexes = [
			models.Index(fields=["class_name"]),
			models.Index(fields=["is_active"]),
		]

	def __str__(self) -> str:
		return f"{self.class_name} → {self.product.sku}"
