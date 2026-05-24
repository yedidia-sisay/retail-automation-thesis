from __future__ import annotations

from rest_framework import serializers

from apps.vision.models import CameraConfig, DetectedObject, DetectionRun


class CameraConfigSerializer(serializers.ModelSerializer):
	"""Full read/write serializer for CameraConfig.

	Validates that the required source-specific field is present for the
	chosen source_type.
	"""

	class Meta:
		model = CameraConfig
		fields = (
			"id",
			"terminal_id",
			"camera_role",
			"source_type",
			"is_active",
			"mock_folder_path",
			"usb_device_index",
			"stream_url",
			"frame_interval_ms",
			"created_at",
			"updated_at",
		)
		read_only_fields = ("id", "terminal_id", "camera_role", "created_at", "updated_at")

	def validate(self, attrs):
		# When PATCHing, merge with existing instance values so partial updates work.
		instance = self.instance
		source_type = attrs.get(
			"source_type",
			getattr(instance, "source_type", None) if instance else None,
		)

		mock_folder_path = attrs.get(
			"mock_folder_path",
			getattr(instance, "mock_folder_path", None) if instance else None,
		)
		usb_device_index = attrs.get(
			"usb_device_index",
			getattr(instance, "usb_device_index", None) if instance else None,
		)
		stream_url = attrs.get(
			"stream_url",
			getattr(instance, "stream_url", None) if instance else None,
		)

		if source_type == CameraConfig.SourceType.MOCK_FOLDER:
			if not (mock_folder_path or "").strip():
				raise serializers.ValidationError(
					{"mock_folder_path": "mock_folder_path is required when source_type is MOCK_FOLDER."}
				)
		elif source_type == CameraConfig.SourceType.USB:
			if usb_device_index is None:
				raise serializers.ValidationError(
					{"usb_device_index": "usb_device_index is required when source_type is USB."}
				)
		elif source_type == CameraConfig.SourceType.NETWORK:
			if not (stream_url or "").strip():
				raise serializers.ValidationError(
					{"stream_url": "stream_url is required when source_type is NETWORK."}
				)

		return attrs


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
