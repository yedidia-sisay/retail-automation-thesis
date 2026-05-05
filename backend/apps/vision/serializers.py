from __future__ import annotations

from rest_framework import serializers

from apps.vision.models import DetectedObject, DetectionRun


class DetectedObjectSerializer(serializers.ModelSerializer):
	bbox = serializers.SerializerMethodField()
	matched_product = serializers.IntegerField(source="matched_product_id", allow_null=True, read_only=True)

	class Meta:
		model = DetectedObject
		fields = (
			"id",
			"class_name",
			"confidence",
			"matched_product",
			"review_status",
			"bbox",
			"created_at",
		)
		read_only_fields = fields

	def get_bbox(self, obj: DetectedObject):
		return [
			float(obj.bbox_x1),
			float(obj.bbox_y1),
			float(obj.bbox_x2),
			float(obj.bbox_y2),
		]


class DetectionRunSerializer(serializers.ModelSerializer):
	objects = DetectedObjectSerializer(source="detected_objects", many=True, read_only=True)

	class Meta:
		model = DetectionRun
		fields = (
			"id",
			"checkout_session",
			"image",
			"model_version",
			"status",
			"error_message",
			"created_at",
			"objects",
		)
		read_only_fields = fields


class VisionDetectUploadSerializer(serializers.Serializer):
	checkout_session_id = serializers.IntegerField()
	image = serializers.ImageField()
