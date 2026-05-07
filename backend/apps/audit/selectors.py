from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count, Q, Sum
from django.utils.dateparse import parse_date

from apps.audit.models import ReceiptEvaluation
from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession
from apps.erp.models import ERPSyncLog
from apps.payments.models import Payment
from apps.receipts.models import Receipt
from apps.vision.models import DetectedObject, DetectionRun


def _parse_date(value: str | None) -> date | None:
	if not value:
		return None
	return parse_date(value)


def _apply_date_filters(qs, *, field: str, start_date: date | None, end_date: date | None):
	if start_date is not None:
		qs = qs.filter(**{f"{field}__date__gte": start_date})
	if end_date is not None:
		qs = qs.filter(**{f"{field}__date__lte": end_date})
	return qs


def _quantize_money(value: Decimal | None) -> Decimal:
	return (value or Decimal("0.00")).quantize(Decimal("0.01"))


def get_transaction_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	sessions_qs = _apply_date_filters(CheckoutSession.objects.all(), field="created_at", start_date=start, end_date=end)

	total_sessions = sessions_qs.count()
	completed_sessions = sessions_qs.filter(status=CheckoutSession.Status.COMPLETED).count()
	cancelled_sessions = sessions_qs.filter(status=CheckoutSession.Status.CANCELLED).count()

	paid_receipts_qs = _apply_date_filters(
		Receipt.objects.filter(payment_status=Receipt.PaymentStatus.PAID),
		field="created_at",
		start_date=start,
		end_date=end,
	)
	paid_sessions = paid_receipts_qs.values("checkout_session_id").distinct().count()

	agg = paid_receipts_qs.aggregate(total=Sum("total"))
	total_revenue = _quantize_money(agg.get("total"))

	# Duration: prefer completed_at, else confirmed_at.
	durations: list[float] = []
	for s in sessions_qs.only("created_at", "confirmed_at", "completed_at"):
		end_ts = getattr(s, "completed_at", None) or s.confirmed_at
		if s.created_at and end_ts:
			durations.append((end_ts - s.created_at).total_seconds())
	average_duration = sum(durations) / len(durations) if durations else 0.0

	return {
		"total_sessions": total_sessions,
		"completed_sessions": completed_sessions,
		"cancelled_sessions": cancelled_sessions,
		"paid_sessions": paid_sessions,
		"total_revenue": str(total_revenue),
		"average_checkout_duration_seconds": round(average_duration, 2),
	}


def get_source_breakdown(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	sessions_qs = _apply_date_filters(CheckoutSession.objects.all(), field="created_at", start_date=start, end_date=end)

	items_qs = CheckoutItem.objects.filter(checkout_session__in=sessions_qs).exclude(status=CheckoutItem.Status.REMOVED).exclude(
		review_status=CheckoutItem.ReviewStatus.REJECTED
	)

	counts = dict(
		items_qs.values("source").annotate(c=Count("id")).values_list("source", "c")
	)

	return {
		"VISION": int(counts.get(CheckoutItem.Source.VISION, 0)),
		"BARCODE": int(counts.get(CheckoutItem.Source.BARCODE, 0)),
		"MANUAL": int(counts.get(CheckoutItem.Source.MANUAL, 0)),
		"WEIGHTED": int(counts.get(CheckoutItem.Source.WEIGHTED, 0)),
	}


def get_correction_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	corrections_qs = _apply_date_filters(CheckoutCorrection.objects.all(), field="created_at", start_date=start, end_date=end)
	corrections_qs = corrections_qs.select_related("checkout_session")

	total_corrections = corrections_qs.count()
	sessions_with_corrections = corrections_qs.values("checkout_session_id").distinct().count()

	accepted_count = corrections_qs.filter(correction_type=CheckoutCorrection.CorrectionType.ACCEPT_ITEM).count()
	rejected_count = corrections_qs.filter(correction_type=CheckoutCorrection.CorrectionType.REJECT_ITEM).count()
	replaced_count = corrections_qs.filter(correction_type=CheckoutCorrection.CorrectionType.REPLACE_PRODUCT).count()
	quantity_changed_count = corrections_qs.filter(correction_type=CheckoutCorrection.CorrectionType.CHANGE_QUANTITY).count()

	total_sessions = _apply_date_filters(CheckoutSession.objects.all(), field="created_at", start_date=start, end_date=end).count()
	correction_rate_per_session = (sessions_with_corrections / total_sessions) if total_sessions else 0.0

	return {
		"total_corrections": total_corrections,
		"accepted_count": accepted_count,
		"rejected_count": rejected_count,
		"replaced_count": replaced_count,
		"quantity_changed_count": quantity_changed_count,
		"sessions_with_corrections": sessions_with_corrections,
		"correction_rate_per_session": round(correction_rate_per_session, 4),
	}


def get_barcode_fallback_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	sessions_qs = _apply_date_filters(CheckoutSession.objects.all(), field="created_at", start_date=start, end_date=end)

	barcode_items_qs = (
		CheckoutItem.objects.filter(checkout_session__in=sessions_qs, source=CheckoutItem.Source.BARCODE)
		.exclude(status=CheckoutItem.Status.REMOVED)
		.exclude(review_status=CheckoutItem.ReviewStatus.REJECTED)
	)

	barcode_item_count = barcode_items_qs.count()
	sessions_using_barcode = barcode_items_qs.values("checkout_session_id").distinct().count()

	total_sessions = sessions_qs.count()
	barcode_fallback_rate = (sessions_using_barcode / total_sessions) if total_sessions else 0.0

	return {
		"barcode_item_count": barcode_item_count,
		"sessions_using_barcode": sessions_using_barcode,
		"barcode_fallback_rate": round(barcode_fallback_rate, 4),
	}


def get_detection_review_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	runs_qs = DetectionRun.objects.select_related("checkout_session")
	runs_qs = _apply_date_filters(runs_qs, field="created_at", start_date=start, end_date=end)

	total_detection_runs = runs_qs.count()

	objects_qs = DetectedObject.objects.filter(detection_run__in=runs_qs)
	total_detected_objects = objects_qs.count()

	auto_accepted_count = objects_qs.filter(review_status=DetectedObject.ReviewStatus.AUTO_ACCEPTED).count()
	needs_review_count = objects_qs.filter(review_status=DetectedObject.ReviewStatus.NEEDS_REVIEW).count()
	rejected_count = objects_qs.filter(review_status=DetectedObject.ReviewStatus.REJECTED_LOW_CONFIDENCE).count()
	unknown_count = objects_qs.filter(review_status=DetectedObject.ReviewStatus.UNKNOWN_CLASS).count()

	avg_conf = objects_qs.aggregate(avg=Avg("confidence")).get("avg")
	average_confidence = float(avg_conf) if avg_conf is not None else 0.0

	return {
		"total_detection_runs": total_detection_runs,
		"total_detected_objects": total_detected_objects,
		"auto_accepted_count": auto_accepted_count,
		"needs_review_count": needs_review_count,
		"rejected_count": rejected_count,
		"unknown_count": unknown_count,
		"average_confidence": round(average_confidence, 4),
	}


def get_receipt_correctness_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	receipts_qs = _apply_date_filters(Receipt.objects.all(), field="created_at", start_date=start, end_date=end)
	total_receipts = receipts_qs.count()

	evals_qs = ReceiptEvaluation.objects.filter(receipt__in=receipts_qs)
	receipts_marked_correct = evals_qs.filter(is_correct=True).count()
	receipts_marked_incorrect = evals_qs.filter(is_correct=False).count()
	unchecked_receipts = total_receipts - evals_qs.count()

	evaluated = receipts_marked_correct + receipts_marked_incorrect
	receipt_correctness_rate = (receipts_marked_correct / evaluated) if evaluated else 0.0

	return {
		"total_receipts": total_receipts,
		"receipts_marked_correct": receipts_marked_correct,
		"receipts_marked_incorrect": receipts_marked_incorrect,
		"unchecked_receipts": unchecked_receipts,
		"receipt_correctness_rate": round(receipt_correctness_rate, 4),
	}


def get_payment_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	payments_qs = _apply_date_filters(Payment.objects.all(), field="created_at", start_date=start, end_date=end)

	return {
		"total_payments": payments_qs.count(),
		"completed_payments": payments_qs.filter(status=Payment.Status.COMPLETED).count(),
		"failed_payments": payments_qs.filter(status=Payment.Status.FAILED).count(),
		"cancelled_payments": payments_qs.filter(status=Payment.Status.CANCELLED).count(),
		"pending_payments": payments_qs.filter(status=Payment.Status.PENDING).count(),
	}


def get_erp_sync_summary(*, start_date: str | None = None, end_date: str | None = None) -> dict[str, int]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	logs_qs = _apply_date_filters(ERPSyncLog.objects.all(), field="created_at", start_date=start, end_date=end)

	retry_required_count = _apply_date_filters(
		Receipt.objects.filter(erp_status=Receipt.ERPStatus.RETRY_REQUIRED),
		field="created_at",
		start_date=start,
		end_date=end,
	).count()

	return {
		"total_sync_attempts": logs_qs.count(),
		"successful_syncs": logs_qs.filter(status=ERPSyncLog.Status.SUCCESS).count(),
		"failed_syncs": logs_qs.filter(status=ERPSyncLog.Status.FAILED).count(),
		"retry_required_count": retry_required_count,
	}


def list_transactions(
	*,
	start_date: str | None = None,
	end_date: str | None = None,
	status: str | None = None,
	cashier: int | None = None,
	payment_status: str | None = None,
	erp_status: str | None = None,
) -> list[dict[str, Any]]:
	start = _parse_date(start_date)
	end = _parse_date(end_date)

	qs = CheckoutSession.objects.all().select_related("cashier", "receipt")
	qs = _apply_date_filters(qs, field="created_at", start_date=start, end_date=end)

	if status:
		qs = qs.filter(status=status)
	if cashier:
		qs = qs.filter(cashier_id=cashier)
	if payment_status:
		qs = qs.filter(receipt__payment_status=payment_status)
	if erp_status:
		qs = qs.filter(receipt__erp_status=erp_status)

	countable_items_filter = ~Q(items__status=CheckoutItem.Status.REMOVED) & ~Q(
		items__review_status=CheckoutItem.ReviewStatus.REJECTED
	)

	qs = qs.annotate(
		item_count=Count("items", filter=countable_items_filter, distinct=True),
		vision_item_count=Count(
			"items",
			filter=countable_items_filter & Q(items__source=CheckoutItem.Source.VISION),
			distinct=True,
		),
		barcode_item_count=Count(
			"items",
			filter=countable_items_filter & Q(items__source=CheckoutItem.Source.BARCODE),
			distinct=True,
		),
		manual_item_count=Count(
			"items",
			filter=countable_items_filter & Q(items__source=CheckoutItem.Source.MANUAL),
			distinct=True,
		),
		weighted_item_count=Count(
			"items",
			filter=countable_items_filter & Q(items__source=CheckoutItem.Source.WEIGHTED),
			distinct=True,
		),
		correction_count=Count("corrections", distinct=True),
	)

	results: list[dict[str, Any]] = []
	for s in qs.order_by("-created_at"):
		receipt = getattr(s, "receipt", None)
		end_ts = getattr(s, "completed_at", None) or s.confirmed_at
		duration_seconds = (end_ts - s.created_at).total_seconds() if (s.created_at and end_ts) else None

		results.append(
			{
				"checkout_session_id": s.id,
				"cashier": getattr(s.cashier, "username", None) if s.cashier else None,
				"cashier_id": s.cashier_id,
				"status": s.status,
				"created_at": s.created_at.isoformat() if s.created_at else None,
				"confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
				"completed_at": getattr(s, "completed_at", None).isoformat() if getattr(s, "completed_at", None) else None,
				"duration_seconds": round(duration_seconds, 2) if duration_seconds is not None else None,
				"total_amount": str(_quantize_money(s.total_amount)),
				"item_count": int(getattr(s, "item_count", 0) or 0),
				"vision_item_count": int(getattr(s, "vision_item_count", 0) or 0),
				"barcode_item_count": int(getattr(s, "barcode_item_count", 0) or 0),
				"manual_item_count": int(getattr(s, "manual_item_count", 0) or 0),
				"weighted_item_count": int(getattr(s, "weighted_item_count", 0) or 0),
				"correction_count": int(getattr(s, "correction_count", 0) or 0),
				"receipt_id": getattr(receipt, "id", None),
				"receipt_number": getattr(receipt, "receipt_number", None),
				"payment_status": getattr(receipt, "payment_status", None),
				"erp_status": getattr(receipt, "erp_status", None),
			}
		)

	return results
