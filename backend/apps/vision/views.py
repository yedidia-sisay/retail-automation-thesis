from __future__ import annotations

import os
import tempfile
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkout.models import CheckoutSession
from apps.vision.camera_sources import CameraSourceError, MockFolderCameraSource, NetworkCameraSource, get_camera_source
from apps.vision.models import CameraConfig, DetectionRun
from apps.vision.serializers import (
	CameraConfigSerializer,
	DetectedObjectSerializer,
	DetectionRunSerializer,
	VisionDetectUploadSerializer,
)
from apps.vision.services import run_detection_for_checkout


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_role(role: str) -> str:
	"""Normalize URL path segment (sku/weighted) to model choice (SKU/WEIGHTED)."""
	return role.upper()


def _get_or_create_camera_config(terminal_id: str, camera_role: str) -> CameraConfig | None:
	"""Return the CameraConfig for a terminal+role, creating a default if absent."""
	role = _normalize_role(camera_role)
	if role not in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
		return None

	config, _ = CameraConfig.objects.get_or_create(
		terminal_id=terminal_id,
		camera_role=role,
		defaults={
			"source_type": CameraConfig.SourceType.MOCK_FOLDER,
			"mock_folder_path": f"media/mock_camera/{role.lower()}/",
			"is_active": True,
		},
	)
	return config


# ---------------------------------------------------------------------------
# Camera settings views
# ---------------------------------------------------------------------------

class CameraListAPIView(APIView):
	"""GET /api/terminals/{terminal_id}/cameras/

	Returns both camera configs (SKU and WEIGHTED) for a terminal.
	Creates default configs if they don't exist yet.
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request, terminal_id: str):
		configs = []
		for role in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
			config, _ = CameraConfig.objects.get_or_create(
				terminal_id=terminal_id,
				camera_role=role,
				defaults={
					"source_type": CameraConfig.SourceType.MOCK_FOLDER,
					"mock_folder_path": f"media/mock_camera/{role.lower()}/",
					"is_active": True,
				},
			)
			configs.append(config)
		serializer = CameraConfigSerializer(configs, many=True)
		return Response(serializer.data)


class CameraSettingsAPIView(APIView):
	"""GET/PATCH /api/terminals/{terminal_id}/cameras/{camera_role}/settings/

	GET  — returns the current config for this terminal+role.
	PATCH — updates source_type and the corresponding source details.
	"""
	permission_classes = [IsAuthenticated]

	def _get_config(self, terminal_id: str, camera_role: str) -> CameraConfig | None:
		role = _normalize_role(camera_role)
		if role not in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
			return None
		config, _ = CameraConfig.objects.get_or_create(
			terminal_id=terminal_id,
			camera_role=role,
			defaults={
				"source_type": CameraConfig.SourceType.MOCK_FOLDER,
				"mock_folder_path": f"media/mock_camera/{role.lower()}/",
				"is_active": True,
			},
		)
		return config

	def get(self, request, terminal_id: str, camera_role: str):
		config = self._get_config(terminal_id, camera_role)
		if config is None:
			return Response(
				{"detail": f"Unknown camera_role '{camera_role}'. Use 'sku' or 'weighted'."},
				status=status.HTTP_404_NOT_FOUND,
			)
		serializer = CameraConfigSerializer(config)
		return Response(serializer.data)

	def patch(self, request, terminal_id: str, camera_role: str):
		config = self._get_config(terminal_id, camera_role)
		if config is None:
			return Response(
				{"detail": f"Unknown camera_role '{camera_role}'. Use 'sku' or 'weighted'."},
				status=status.HTTP_404_NOT_FOUND,
			)
		serializer = CameraConfigSerializer(config, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)


class CameraTestAPIView(APIView):
	"""POST /api/terminals/{terminal_id}/cameras/{camera_role}/test/

	Attempts to read one frame from the configured camera source.
	Returns {"ok": true/false, "message": "..."}.
	"""
	permission_classes = [IsAuthenticated]

	def post(self, request, terminal_id: str, camera_role: str):
		role = _normalize_role(camera_role)
		if role not in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
			return Response(
				{"ok": False, "message": f"Unknown camera_role '{camera_role}'."},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			config = CameraConfig.objects.get(terminal_id=terminal_id, camera_role=role)
		except CameraConfig.DoesNotExist:
			return Response(
				{"ok": False, "message": "Camera config not found. Save settings first."},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			source = get_camera_source(config)
			source.get_current_frame()
			return Response({"ok": True, "message": "Camera source is readable."})
		except CameraSourceError as exc:
			return Response({"ok": False, "message": str(exc)})
		except Exception as exc:
			return Response({"ok": False, "message": f"Unexpected error: {exc}"})


class CameraPreviewAPIView(APIView):
	"""GET /api/terminals/{terminal_id}/cameras/{camera_role}/preview/

	Returns the current frame as a JPEG image response.
	Used for mock/USB sources where the backend must proxy the frame.
	For NETWORK sources, use the stream-url endpoint instead so the browser
	can connect to the camera directly.
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request, terminal_id: str, camera_role: str):
		role = _normalize_role(camera_role)
		if role not in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
			return Response(
				{"detail": f"Unknown camera_role '{camera_role}'."},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			config = CameraConfig.objects.get(terminal_id=terminal_id, camera_role=role)
		except CameraConfig.DoesNotExist:
			return Response(
				{"detail": "Camera config not found. Configure the camera source first."},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			source = get_camera_source(config)
			frame_bytes = source.get_current_frame()
			response = HttpResponse(frame_bytes, content_type="image/jpeg")
			# Prevent any caching so each request always returns a fresh frame.
			response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
			response["Pragma"] = "no-cache"
			response["Expires"] = "0"
			return response
		except CameraSourceError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
		except Exception as exc:
			return Response(
				{"detail": f"Could not read camera frame: {exc}"},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)


class CameraStreamInfoAPIView(APIView):
	"""GET /api/terminals/{terminal_id}/cameras/{camera_role}/stream-info/

	Returns information about how the frontend should display this camera.

	For NETWORK sources this returns the direct stream URL so the browser can
	connect to the camera without going through Django on every frame.  The
	browser renders MJPEG streams natively in an <img> tag.

	Response shape:
	  {
	    "source_type": "NETWORK" | "USB" | "MOCK_FOLDER",
	    "stream_url": "http://..." | null,   // direct URL for NETWORK sources
	    "use_direct_stream": true | false,   // true when frontend should use stream_url
	  }
	"""
	permission_classes = [IsAuthenticated]

	def get(self, request, terminal_id: str, camera_role: str):
		role = _normalize_role(camera_role)
		if role not in (CameraConfig.CameraRole.SKU, CameraConfig.CameraRole.WEIGHTED):
			return Response(
				{"detail": f"Unknown camera_role '{camera_role}'."},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			config = CameraConfig.objects.get(terminal_id=terminal_id, camera_role=role)
		except CameraConfig.DoesNotExist:
			return Response(
				{"detail": "Camera config not found."},
				status=status.HTTP_404_NOT_FOUND,
			)

		is_network = config.source_type == CameraConfig.SourceType.NETWORK
		stream_url = None
		if is_network:
			try:
				source = get_camera_source(config)
				if isinstance(source, NetworkCameraSource):
					stream_url = source.get_stream_url()
			except CameraSourceError:
				pass

		return Response({
			"source_type": config.source_type,
			"stream_url": stream_url,
			"use_direct_stream": is_network and stream_url is not None,
		})


# ---------------------------------------------------------------------------
# Detection endpoints
# ---------------------------------------------------------------------------

class DetectSKUFrameAPIView(APIView):
	"""POST /api/terminals/{terminal_id}/vision/detect-sku-frame/

	1. Loads CameraConfig for terminal_id + SKU.
	2. Reads the current frame from the camera source.
	3. Saves the frame under media/checkout_frames/.
	4. Runs YOLO detection via the existing run_detection_for_checkout service.
	5. Returns draft items in the same format as the existing vision/detect/ endpoint.

	Request body (JSON):
	  { "checkout_session_id": <int> }
	"""
	permission_classes = [IsAuthenticated]

	def post(self, request, terminal_id: str):
		session_id = request.data.get("checkout_session_id")
		if not session_id:
			return Response(
				{"detail": "checkout_session_id is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		session = get_object_or_404(CheckoutSession, pk=session_id)

		try:
			config = CameraConfig.objects.get(
				terminal_id=terminal_id,
				camera_role=CameraConfig.CameraRole.SKU,
			)
		except CameraConfig.DoesNotExist:
			return Response(
				{
					"camera_role": "SKU",
					"source_type": None,
					"detections": [],
					"draft_items": [],
					"message": "SKU camera not configured for this terminal. Set up the camera source first.",
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		# Build camera source.
		try:
			source = get_camera_source(config)
		except CameraSourceError as exc:
			return Response(
				{
					"camera_role": "SKU",
					"source_type": config.source_type,
					"detections": [],
					"draft_items": [],
					"message": str(exc),
				},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		# For MockFolderCameraSource we can get the actual file path directly,
		# which avoids writing a temp file and gives DetectionRun a real path.
		frame_file = None
		tmp_path = None

		try:
			from django.core.files import File as DjangoFile

			if isinstance(source, MockFolderCameraSource):
				image_path = source.get_current_frame_path()
				frame_file = DjangoFile(open(image_path, "rb"), name=image_path.name)
			else:
				frame_bytes = source.get_current_frame()
				tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
				tmp.write(frame_bytes)
				tmp.close()
				tmp_path = tmp.name
				frame_file = DjangoFile(open(tmp_path, "rb"), name=f"frame_{terminal_id}_sku.jpg")
		except CameraSourceError as exc:
			return Response(
				{
					"camera_role": "SKU",
					"source_type": config.source_type,
					"detections": [],
					"draft_items": [],
					"message": str(exc),
				},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		try:
			user = request.user if getattr(request.user, "is_authenticated", False) else None
			result = run_detection_for_checkout(
				checkout_session=session,
				image_file=frame_file,
				user=user,
			)

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
					"camera_role": "SKU",
					"source_type": config.source_type,
					"detection_run_id": run.id,
					"status": run.status,
					"detections": detections,
					"draft_items": draft_items,
					"message": f"Frame captured and detection completed. {len(draft_items)} item(s) found.",
				}
			)
		except Exception as exc:
			return Response(
				{
					"camera_role": "SKU",
					"source_type": config.source_type,
					"detections": [],
					"draft_items": [],
					"message": f"Detection failed: {exc}",
				},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)
		finally:
			if frame_file:
				frame_file.close()
			if tmp_path and os.path.exists(tmp_path):
				os.unlink(tmp_path)


class DetectWeightedFrameAPIView(APIView):
	"""POST /api/terminals/{terminal_id}/vision/detect-weighted-frame/

	1. Loads CameraConfig for terminal_id + WEIGHTED.
	2. Reads the current frame from the camera source.
	3. Returns a structured placeholder response (weighted OCR/model pending).

	The response shape is designed so that when weighted detection/OCR is
	implemented, the same fields can be populated without changing the
	frontend contract.

	Request body (JSON):
	  { "checkout_session_id": <int> }
	"""
	permission_classes = [IsAuthenticated]

	def post(self, request, terminal_id: str):
		session_id = request.data.get("checkout_session_id")
		if not session_id:
			return Response(
				{"detail": "checkout_session_id is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		# Validate session exists.
		get_object_or_404(CheckoutSession, pk=session_id)

		try:
			config = CameraConfig.objects.get(
				terminal_id=terminal_id,
				camera_role=CameraConfig.CameraRole.WEIGHTED,
			)
		except CameraConfig.DoesNotExist:
			return Response(
				{
					"camera_role": "WEIGHTED",
					"source_type": None,
					"detected_product": None,
					"weight_value": None,
					"weight_source": "MANUAL_REQUIRED",
					"message": "Weighted camera not configured for this terminal. Set up the camera source first.",
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			source = get_camera_source(config)
		except CameraSourceError as exc:
			return Response(
				{
					"camera_role": "WEIGHTED",
					"source_type": config.source_type,
					"detected_product": None,
					"weight_value": None,
					"weight_source": "MANUAL_REQUIRED",
					"message": str(exc),
				},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		# Validate the source is readable.
		try:
			if isinstance(source, MockFolderCameraSource):
				source.get_current_frame_path()
			else:
				source.get_current_frame()
		except CameraSourceError as exc:
			return Response(
				{
					"camera_role": "WEIGHTED",
					"source_type": config.source_type,
					"detected_product": None,
					"weight_value": None,
					"weight_source": "MANUAL_REQUIRED",
					"message": str(exc),
				},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		# Weighted detection / OCR is not yet implemented.
		return Response(
			{
				"camera_role": "WEIGHTED",
				"source_type": config.source_type,
				"detected_product": None,
				"weight_value": None,
				"weight_source": "MANUAL_REQUIRED",
				"unit_price": None,
				"subtotal": None,
				"message": "Weighted frame captured successfully. Weighted detection/OCR pending — please enter weight manually.",
			}
		)


# ---------------------------------------------------------------------------
# Existing vision views (unchanged)
# ---------------------------------------------------------------------------

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
				"timing": result.timing,
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
		return Response(DetectionRunSerializer(run).data)
