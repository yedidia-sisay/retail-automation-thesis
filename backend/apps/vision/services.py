from __future__ import annotations

from dataclasses import dataclass
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


def _to_decimal(value, *, places: str) -> Decimal:
	return Decimal(str(value)).quantize(Decimal(places))


def run_detection_for_checkout(*, checkout_session: CheckoutSession, image_file, user=None) -> DetectionResult:
	"""Run YOLO detection for an editable checkout session and create draft items."""

	if not checkout_session.is_editable:
		raise ValidationError({"detail": "This checkout session is not editable."})

	model_version = ModelVersion.objects.filter(is_active=True).order_by("-created_at").first()

	detection_run = DetectionRun.objects.create(
		checkout_session=checkout_session,
		image=image_file,
		model_version=model_version,
		status=DetectionRun.Status.PENDING,
	)

	client = YOLOClient()
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

		mapped = get_product_for_detection_class(class_name)
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

	return DetectionResult(detection_run=detection_run, draft_items=draft_items)
