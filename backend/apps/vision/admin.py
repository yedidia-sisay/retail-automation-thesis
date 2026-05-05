from django.contrib import admin

from apps.vision.models import DetectedObject, DetectionRun, ModelVersion


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
	list_display = ("name", "version", "is_active", "model_path", "created_at")
	list_filter = ("is_active", "created_at")
	search_fields = ("name", "version", "model_path")


@admin.register(DetectionRun)
class DetectionRunAdmin(admin.ModelAdmin):
	list_display = ("id", "checkout_session", "status", "model_version", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("=id", "checkout_session__id")
	list_select_related = ("checkout_session", "model_version")
	readonly_fields = ("created_at", "updated_at")


@admin.register(DetectedObject)
class DetectedObjectAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"detection_run",
		"class_name",
		"confidence",
		"matched_product",
		"review_status",
		"created_at",
	)
	list_filter = ("review_status", "created_at")
	search_fields = ("class_name", "matched_product__name", "matched_product__sku")
	list_select_related = ("detection_run", "matched_product")
	readonly_fields = ("created_at",)
