from __future__ import annotations

from django.db import models

from apps.catalog.models import Product
from apps.checkout.models import CheckoutSession


class ModelVersion(models.Model):
	name = models.CharField(max_length=255)
	version = models.CharField(max_length=255)
	model_path = models.CharField(max_length=1024, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["is_active", "created_at"]),
			models.Index(fields=["name", "version"]),
		]

	def __str__(self) -> str:
		return f"{self.name} ({self.version})"


class DetectionRun(models.Model):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		COMPLETED = "COMPLETED", "Completed"
		FAILED = "FAILED", "Failed"

	checkout_session = models.ForeignKey(
		CheckoutSession,
		on_delete=models.CASCADE,
		related_name="detection_runs",
	)
	image = models.ImageField(upload_to="checkout_frames/")
	model_version = models.ForeignKey(
		ModelVersion,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="detection_runs",
	)
	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.PENDING,
	)
	raw_output = models.JSONField(default=dict, blank=True)
	error_message = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)
		indexes = [
			models.Index(fields=["checkout_session", "created_at"]),
			models.Index(fields=["status", "created_at"]),
		]

	def __str__(self) -> str:
		return f"DetectionRun #{self.pk} ({self.status})"


class DetectedObject(models.Model):
	class ReviewStatus(models.TextChoices):
		AUTO_ACCEPTED = "AUTO_ACCEPTED", "Auto accepted"
		NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"
		REJECTED_LOW_CONFIDENCE = "REJECTED_LOW_CONFIDENCE", "Rejected: low confidence"
		UNKNOWN_CLASS = "UNKNOWN_CLASS", "Unknown class"

	detection_run = models.ForeignKey(
		DetectionRun,
		on_delete=models.CASCADE,
		related_name="detected_objects",
	)
	class_name = models.CharField(max_length=255)
	confidence = models.DecimalField(max_digits=5, decimal_places=4)
	bbox_x1 = models.DecimalField(max_digits=10, decimal_places=2)
	bbox_y1 = models.DecimalField(max_digits=10, decimal_places=2)
	bbox_x2 = models.DecimalField(max_digits=10, decimal_places=2)
	bbox_y2 = models.DecimalField(max_digits=10, decimal_places=2)
	matched_product = models.ForeignKey(
		Product,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="detected_objects",
	)
	review_status = models.CharField(max_length=32, choices=ReviewStatus.choices)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("created_at",)
		indexes = [
			models.Index(fields=["detection_run", "created_at"]),
			models.Index(fields=["class_name"]),
			models.Index(fields=["review_status"]),
			models.Index(fields=["matched_product"]),
		]

	def __str__(self) -> str:
		return f"{self.class_name} ({self.confidence})"
