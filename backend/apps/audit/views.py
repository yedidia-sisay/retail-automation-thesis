from __future__ import annotations

import csv
import json

from django.http import HttpResponse
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import ReceiptEvaluation
from apps.audit.selectors import (
	get_barcode_fallback_summary,
	get_correction_summary,
	get_detection_review_summary,
	get_erp_sync_summary,
	get_payment_summary,
	get_receipt_correctness_summary,
	get_source_breakdown,
	get_transaction_summary,
	list_transactions,
)
from apps.audit.serializers import ReceiptEvaluationSerializer
from apps.checkout.models import CheckoutCorrection
from apps.vision.models import DetectedObject


class ReceiptEvaluationListCreateAPIView(ListCreateAPIView):
	permission_classes = [AllowAny]
	serializer_class = ReceiptEvaluationSerializer
	queryset = ReceiptEvaluation.objects.select_related("receipt", "evaluated_by").order_by("-created_at")


class ReceiptEvaluationDetailAPIView(RetrieveUpdateAPIView):
	permission_classes = [AllowAny]
	serializer_class = ReceiptEvaluationSerializer
	queryset = ReceiptEvaluation.objects.select_related("receipt", "evaluated_by").all()
	lookup_field = "pk"


class DashboardSummaryAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_transaction_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardTransactionsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = list_transactions(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
			status=request.query_params.get("status"),
			cashier=int(request.query_params["cashier"]) if request.query_params.get("cashier") else None,
			payment_status=request.query_params.get("payment_status"),
			erp_status=request.query_params.get("erp_status"),
		)
		return Response({"results": data})


class DashboardItemSourcesAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_source_breakdown(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardCorrectionsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_correction_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardBarcodeFallbackAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_barcode_fallback_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardDetectionsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_detection_review_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardReceiptCorrectnessAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_receipt_correctness_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardPaymentsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_payment_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class DashboardERPSyncAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = get_erp_sync_summary(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
		)
		return Response(data)


class TransactionsAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		data = list_transactions(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
			status=request.query_params.get("status"),
			cashier=int(request.query_params["cashier"]) if request.query_params.get("cashier") else None,
			payment_status=request.query_params.get("payment_status"),
			erp_status=request.query_params.get("erp_status"),
		)
		return Response({"results": data})


class TransactionsCSVExportAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		rows = list_transactions(
			start_date=request.query_params.get("start_date"),
			end_date=request.query_params.get("end_date"),
			status=request.query_params.get("status"),
			cashier=int(request.query_params["cashier"]) if request.query_params.get("cashier") else None,
			payment_status=request.query_params.get("payment_status"),
			erp_status=request.query_params.get("erp_status"),
		)

		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = 'attachment; filename="transactions.csv"'

		writer = csv.writer(response)
		header = [
			"checkout_session_id",
			"cashier",
			"status",
			"created_at",
			"confirmed_at",
			"completed_at",
			"duration_seconds",
			"total_amount",
			"item_count",
			"vision_item_count",
			"barcode_item_count",
			"manual_item_count",
			"weighted_item_count",
			"correction_count",
			"receipt_id",
			"receipt_number",
			"payment_status",
			"erp_status",
		]
		writer.writerow(header)
		for row in rows:
			writer.writerow([row.get(col) for col in header])

		return response


class CorrectionsCSVExportAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		start_date = request.query_params.get("start_date")
		end_date = request.query_params.get("end_date")

		qs = CheckoutCorrection.objects.select_related(
			"checkout_session", "checkout_item", "corrected_by"
		).order_by("created_at")
		if start_date:
			qs = qs.filter(created_at__date__gte=start_date)
		if end_date:
			qs = qs.filter(created_at__date__lte=end_date)

		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = 'attachment; filename="corrections.csv"'
		writer = csv.writer(response)

		header = [
			"correction_id",
			"checkout_session_id",
			"checkout_item_id",
			"correction_type",
			"corrected_by",
			"before_data",
			"after_data",
			"created_at",
		]
		writer.writerow(header)
		for c in qs:
			writer.writerow(
				[
					c.id,
					c.checkout_session_id,
					c.checkout_item_id,
					c.correction_type,
					getattr(c.corrected_by, "username", None) if c.corrected_by else None,
					json.dumps(c.before_data or {}, sort_keys=True),
					json.dumps(c.after_data or {}, sort_keys=True),
					c.created_at.isoformat() if c.created_at else None,
				]
			)
		return response


class DetectionsCSVExportAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		start_date = request.query_params.get("start_date")
		end_date = request.query_params.get("end_date")

		qs = DetectedObject.objects.select_related(
			"detection_run", "detection_run__checkout_session", "matched_product"
		).order_by("created_at")
		if start_date:
			qs = qs.filter(created_at__date__gte=start_date)
		if end_date:
			qs = qs.filter(created_at__date__lte=end_date)

		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = 'attachment; filename="detections.csv"'
		writer = csv.writer(response)

		header = [
			"detection_run_id",
			"detected_object_id",
			"checkout_session_id",
			"class_name",
			"confidence",
			"matched_product",
			"review_status",
			"created_at",
		]
		writer.writerow(header)
		for obj in qs:
			writer.writerow(
				[
					obj.detection_run_id,
					obj.id,
					obj.detection_run.checkout_session_id,
					obj.class_name,
					str(obj.confidence),
					getattr(obj.matched_product, "sku", None) if obj.matched_product else None,
					obj.review_status,
					obj.created_at.isoformat() if obj.created_at else None,
				]
			)
		return response


class ReceiptEvaluationsCSVExportAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		start_date = request.query_params.get("start_date")
		end_date = request.query_params.get("end_date")

		qs = ReceiptEvaluation.objects.select_related("receipt").order_by("created_at")
		if start_date:
			qs = qs.filter(created_at__date__gte=start_date)
		if end_date:
			qs = qs.filter(created_at__date__lte=end_date)

		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = 'attachment; filename="receipt-evaluations.csv"'
		writer = csv.writer(response)

		header = [
			"receipt_id",
			"receipt_number",
			"is_correct",
			"product_names_correct",
			"quantities_correct",
			"prices_correct",
			"subtotals_correct",
			"total_correct",
			"notes",
			"created_at",
		]
		writer.writerow(header)
		for ev in qs:
			writer.writerow(
				[
					ev.receipt_id,
					ev.receipt.receipt_number,
					ev.is_correct,
					ev.product_names_correct,
					ev.quantities_correct,
					ev.prices_correct,
					ev.subtotals_correct,
					ev.total_correct,
					ev.notes,
					ev.created_at.isoformat() if ev.created_at else None,
				]
			)
		return response
