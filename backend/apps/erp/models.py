from __future__ import annotations

from django.db import models

from apps.catalog.models import Product
from apps.receipts.models import Receipt


class ERPProductMapping(models.Model):
	product = models.ForeignKey(
		Product,
		on_delete=models.CASCADE,
		related_name="erp_mappings",
	)
	erp_system = models.CharField(max_length=50, default="ODOO")
	erp_product_id = models.CharField(max_length=100)
	erp_product_name = models.CharField(max_length=255, blank=True)
	last_synced_at = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("erp_system", "product_id")
		constraints = [
			models.UniqueConstraint(
				fields=["product", "erp_system"],
				name="unique_product_erp_system_mapping",
			)
		]
		indexes = [
			models.Index(fields=["erp_system", "erp_product_id"]),
			models.Index(fields=["product", "erp_system"]),
		]

	def __str__(self) -> str:
		return f"{self.erp_system}:{self.erp_product_id} → {self.product.sku}"


class ERPReceiptMapping(models.Model):
	class SyncStatus(models.TextChoices):
		PENDING = "PENDING", "Pending"
		SYNCED = "SYNCED", "Synced"
		FAILED = "FAILED", "Failed"
		RETRY_REQUIRED = "RETRY_REQUIRED", "Retry required"

	receipt = models.ForeignKey(
		Receipt,
		on_delete=models.CASCADE,
		related_name="erp_mappings",
	)
	erp_system = models.CharField(max_length=50, default="ODOO")
	erp_receipt_id = models.CharField(max_length=100, blank=True, null=True)
	erp_reference = models.CharField(max_length=100, blank=True, null=True)
	sync_status = models.CharField(
		max_length=20,
		choices=SyncStatus.choices,
		default=SyncStatus.PENDING,
	)
	request_payload = models.JSONField(default=dict, blank=True)
	response_payload = models.JSONField(default=dict, blank=True)
	error_message = models.TextField(blank=True)
	synced_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		constraints = [
			models.UniqueConstraint(
				fields=["receipt", "erp_system"],
				name="unique_receipt_erp_system_mapping",
			)
		]
		indexes = [
			models.Index(fields=["erp_system", "sync_status", "created_at"]),
			models.Index(fields=["receipt", "erp_system"]),
		]

	def __str__(self) -> str:
		return f"{self.erp_system}:{self.receipt.receipt_number} ({self.sync_status})"


class ERPSyncLog(models.Model):
	class ObjectType(models.TextChoices):
		PRODUCT = "PRODUCT", "Product"
		RECEIPT = "RECEIPT", "Receipt"
		PAYMENT = "PAYMENT", "Payment"
		TRANSACTION = "TRANSACTION", "Transaction"

	class Action(models.TextChoices):
		SYNC_PRODUCTS = "SYNC_PRODUCTS", "Sync products"
		PUSH_RECEIPT = "PUSH_RECEIPT", "Push receipt"
		RETRY_SYNC = "RETRY_SYNC", "Retry sync"

	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		SUCCESS = "SUCCESS", "Success"
		FAILED = "FAILED", "Failed"

	object_type = models.CharField(max_length=20, choices=ObjectType.choices)
	object_id = models.CharField(max_length=100)
	action = models.CharField(max_length=20, choices=Action.choices)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	erp_system = models.CharField(max_length=50, default="ODOO")
	request_payload = models.JSONField(default=dict, blank=True)
	response_payload = models.JSONField(default=dict, blank=True)
	error_message = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["object_type", "created_at"]),
			models.Index(fields=["action", "created_at"]),
			models.Index(fields=["status", "created_at"]),
			models.Index(fields=["erp_system", "created_at"]),
			models.Index(fields=["object_id"]),
		]

	def __str__(self) -> str:
		return f"{self.action} {self.object_type}:{self.object_id} ({self.status})"
