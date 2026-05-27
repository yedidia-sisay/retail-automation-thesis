from __future__ import annotations

import time
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.audit.services import log_audit_event
from apps.catalog.selectors import get_product_for_detection_class
from apps.checkout.models import CheckoutSession
from apps.checkout.services import CheckoutError, add_detection_results_to_checkout
from apps.vision.models import DetectedObject, DetectionRun, ModelVersion
from apps.vision.yolo_client import YOLOClient


@dataclass(frozen=True)
class DetectionResult:
	detection_run: DetectionRun
	draft_items: list
	# Timing breakdown in milliseconds.  All values are wall-clock durations
	# measured with time.perf_counter() on the Django process.
	timing: dict = field(default_factory=dict)


def _to_decimal(value, *, places: str) -> Decimal:
	return Decimal(str(value)).quantize(Decimal(places))


def run_detection_for_checkout(*, checkout_session: CheckoutSession, image_file, user=None) -> DetectionResult:
	"""Run YOLO detection for an editable checkout session and create draft items."""

	# ── T0: overall start ──────────────────────────────────────────────────
	t_total_start = time.perf_counter()

	if not checkout_session.is_editable:
		raise ValidationError({"detail": "This checkout session is not editable."})

	model_version = ModelVersion.objects.filter(is_active=True).order_by("-created_at").first()

	detection_run = DetectionRun.objects.create(
		checkout_session=checkout_session,
		image=image_file,
		model_version=model_version,
		status=DetectionRun.Status.PENDING,
	)

	# ── Stage 1: YOLO inference (HTTP round-trip to yolo_service) ──────────
	client = YOLOClient()
	t_yolo_start = time.perf_counter()
	try:
		detections = client.detect_from_path(detection_run.image.path)
	except Exception as exc:
		detection_run.status = DetectionRun.Status.FAILED
		detection_run.error_message = str(exc)
		detection_run.save(update_fields=["status", "error_message", "updated_at"])

		log_audit_event(
			user=user,
			checkout_session=checkout_session,
			event_type="VISION_DETECTION_FAILED",
			description="Vision detection failed.",
			metadata={"detection_run_id": detection_run.id, "error": str(exc)},
		)
		raise ValidationError({"detail": "Vision detection failed.", "error": str(exc)})
	t_yolo_end = time.perf_counter()

	# ── Stage 2: detection post-processing + product lookup ────────────────
	# These two stages are tightly coupled inside the same loop (each raw
	# detection is immediately looked up in the DB).  We time them together
	# as one pass and also accumulate the pure DB-lookup cost separately.
	t_postprocess_start = time.perf_counter()
	t_product_lookup_accumulated = 0.0

	objects_to_create: list[DetectedObject] = []
	unknown_count = 0
	low_conf_count = 0

	default_mapping_threshold = Decimal("0.80")
	low_conf_threshold = Decimal("0.50")

	for det in detections:
		class_name = (det.get("class_name") or "").strip()
		confidence = _to_decimal(det.get("confidence", 0), places="0.0001")
		raw_bbox = det.get("bbox") or {}
		# bbox is a dict {"x1": ..., "y1": ..., "x2": ..., "y2": ...}
		if isinstance(raw_bbox, dict):
			bbox_x1 = _to_decimal(raw_bbox.get("x1", 0), places="0.01")
			bbox_y1 = _to_decimal(raw_bbox.get("y1", 0), places="0.01")
			bbox_x2 = _to_decimal(raw_bbox.get("x2", 0), places="0.01")
			bbox_y2 = _to_decimal(raw_bbox.get("y2", 0), places="0.01")
		else:
			# Fallback for legacy list format [x1, y1, x2, y2]
			bbox_list = raw_bbox if len(raw_bbox) == 4 else [0, 0, 0, 0]
			bbox_x1 = _to_decimal(bbox_list[0], places="0.01")
			bbox_y1 = _to_decimal(bbox_list[1], places="0.01")
			bbox_x2 = _to_decimal(bbox_list[2], places="0.01")
			bbox_y2 = _to_decimal(bbox_list[3], places="0.01")

		# ── product lookup (DB) ────────────────────────────────────────────
		_t_lookup = time.perf_counter()
		mapped = get_product_for_detection_class(class_name)
		t_product_lookup_accumulated += time.perf_counter() - _t_lookup

		matched_product = None
		minimum_confidence = default_mapping_threshold
		if mapped is not None:
			matched_product, minimum_confidence = mapped
			minimum_confidence = minimum_confidence or default_mapping_threshold

		if mapped is None:
			review_status = DetectedObject.ReviewStatus.UNKNOWN_CLASS
			unknown_count += 1
			log_audit_event(
				user=user,
				checkout_session=checkout_session,
				event_type="VISION_UNKNOWN_CLASS",
				description="Vision detected an unknown class.",
				metadata={
					"detection_run_id": detection_run.id,
					"class_name": class_name,
					"confidence": str(confidence),
				},
			)
		elif confidence < low_conf_threshold:
			review_status = DetectedObject.ReviewStatus.REJECTED_LOW_CONFIDENCE
			low_conf_count += 1
			log_audit_event(
				user=user,
				checkout_session=checkout_session,
				event_type="VISION_LOW_CONFIDENCE",
				description="Vision detected a product with low confidence.",
				metadata={
					"detection_run_id": detection_run.id,
					"class_name": class_name,
					"confidence": str(confidence),
					"matched_product_id": getattr(matched_product, "id", None),
				},
			)
		elif confidence < minimum_confidence:
			review_status = DetectedObject.ReviewStatus.NEEDS_REVIEW
		else:
			review_status = DetectedObject.ReviewStatus.AUTO_ACCEPTED

		objects_to_create.append(
			DetectedObject(
				detection_run=detection_run,
				class_name=class_name,
				confidence=confidence,
				bbox_x1=bbox_x1,
				bbox_y1=bbox_y1,
				bbox_x2=bbox_x2,
				bbox_y2=bbox_y2,
				matched_product=matched_product,
				review_status=review_status,
			)
		)

	t_postprocess_end = time.perf_counter()

	# ── Stage 3: DB write + draft item (receipt) aggregation ───────────────
	t_receipt_start = time.perf_counter()
	try:
		with transaction.atomic():
			# Store the detection output and objects.
			DetectedObject.objects.bulk_create(objects_to_create)

			detection_run.status = DetectionRun.Status.COMPLETED
			detection_run.raw_output = {"detections": detections}
			detection_run.error_message = ""
			detection_run.save(update_fields=["status", "raw_output", "error_message", "updated_at"])

			# Create draft checkout items from eligible detections.
			draft_items = add_detection_results_to_checkout(
				session=checkout_session,
				detection_run=detection_run,
			)

	except CheckoutError as exc:
		detection_run.status = DetectionRun.Status.FAILED
		detection_run.error_message = str(exc)
		detection_run.save(update_fields=["status", "error_message", "updated_at"])
		raise ValidationError({"detail": str(exc)})
	except Exception as exc:
		detection_run.status = DetectionRun.Status.FAILED
		detection_run.error_message = str(exc)
		detection_run.save(update_fields=["status", "error_message", "updated_at"])
		raise ValidationError({"detail": "Failed to store detection results.", "error": str(exc)})
	t_receipt_end = time.perf_counter()

	# ── T_end: overall end ─────────────────────────────────────────────────
	t_total_end = time.perf_counter()

	def _ms(start: float, end: float) -> float:
		return round((end - start) * 1000.0, 3)

	timing = {
		# Round-trip HTTP POST to yolo_service (includes network + model inference).
		# When USE_MOCK_YOLO=True this is just the mock function call overhead.
		"yolo_inference_ms": _ms(t_yolo_start, t_yolo_end),
		# Iterating raw detections, parsing bboxes, confidence filtering.
		# Excludes the DB lookup cost (tracked separately below).
		"postprocess_ms": _ms(t_postprocess_start, t_postprocess_end) - round(t_product_lookup_accumulated * 1000.0, 3),
		# Accumulated time spent in get_product_for_detection_class() DB queries.
		"product_lookup_ms": round(t_product_lookup_accumulated * 1000.0, 3),
		# bulk_create DetectedObjects + add_detection_results_to_checkout (draft items).
		"receipt_build_ms": _ms(t_receipt_start, t_receipt_end),
		# Wall-clock time from function entry to return (includes all stages above
		# plus Django ORM overhead for DetectionRun.objects.create etc.).
		"total_backend_ms": _ms(t_total_start, t_total_end),
	}

	log_audit_event(
		user=user,
		checkout_session=checkout_session,
		event_type="VISION_DETECTION_COMPLETED",
		description="Vision detection completed.",
		metadata={
			"detection_run_id": detection_run.id,
			"detections_count": len(detections),
			"unknown_count": unknown_count,
			"low_confidence_count": low_conf_count,
		},
	)

	return DetectionResult(detection_run=detection_run, draft_items=draft_items, timing=timing)
