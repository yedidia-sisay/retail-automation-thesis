from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkout.models import CheckoutSession
from apps.vision.models import DetectionRun
from apps.vision.serializers import (
	DetectedObjectSerializer,
	DetectionRunSerializer,
	VisionDetectUploadSerializer,
)
from apps.vision.services import run_detection_for_checkout


class VisionDetectAPIView(APIView):
	permission_classes = [AllowAny]
	parser_classes = [MultiPartParser, FormParser]

	def post(self, request):
		upload = VisionDetectUploadSerializer(data=request.data)
		upload.is_valid(raise_exception=True)

		session_id = upload.validated_data["checkout_session_id"]
		image_file = upload.validated_data["image"]
		session = get_object_or_404(CheckoutSession, pk=session_id)

		user = request.user if getattr(request.user, "is_authenticated", False) else None
		result = run_detection_for_checkout(checkout_session=session, image_file=image_file, user=user)

		run = (
			DetectionRun.objects.select_related("checkout_session", "model_version")
			.prefetch_related("detected_objects")
			.get(pk=result.detection_run.pk)
		)

		detections = DetectedObjectSerializer(run.detected_objects.all(), many=True).data
		draft_items = [
			{
				"product_id": item.product_id,
				"product_name": item.product.name,
				"quantity": str(item.quantity),
				"unit_price": str(item.unit_price),
				"subtotal": str(item.subtotal),
				"source": item.source,
				"needs_review": item.status == item.Status.NEEDS_REVIEW,
			}
			for item in result.draft_items
		]

		return Response(
			{
				"detection_run_id": run.id,
				"status": run.status,
				"detections": detections,
				"draft_items": draft_items,
			},
			status=status.HTTP_200_OK,
		)


class DetectionRunDetailAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, run_id: int):
		run = get_object_or_404(
			DetectionRun.objects.select_related("checkout_session", "model_version").prefetch_related(
				"detected_objects"
			),
			pk=run_id,
		)
		out = DetectionRunSerializer(run)
		return Response(out.data, status=status.HTTP_200_OK)
