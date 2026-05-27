from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.erp.models import ERPProductMapping, ERPReceiptMapping, ERPSyncLog
from apps.erp.serializers import (
	ERPProductMappingSerializer,
	ERPReceiptMappingSerializer,
	ERPSyncLogSerializer,
	SyncProductsSerializer,
)
from apps.erp.services import (
	build_receipt_erp_payload,
	push_receipt_to_erp,
	retry_receipt_erp_sync,
	sync_products_from_erp,
)
from apps.receipts.models import Receipt


class ERPReceiptPayloadPreviewAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, receipt_id: int):
		receipt = Receipt.objects.filter(pk=receipt_id).first()
		if receipt is None:
			return Response({"detail": "Receipt not found."}, status=status.HTTP_404_NOT_FOUND)

		payload = build_receipt_erp_payload(receipt)
		return Response(payload, status=status.HTTP_200_OK)


class ERPPushReceiptAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, receipt_id: int):
		result = push_receipt_to_erp(
			receipt_id=receipt_id,
			user=request.user if getattr(request.user, "is_authenticated", False) else None,
		)
		data = {
			"receipt_id": result.receipt_id,
			"erp_status": result.erp_status,
			"erp_reference": result.erp_reference,
			"message": result.message,
		}
		if result.error:
			data["error"] = result.error
		return Response(data, status=status.HTTP_200_OK)


class ERPRetryReceiptAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, receipt_id: int):
		result = retry_receipt_erp_sync(
			receipt_id=receipt_id,
			user=request.user if getattr(request.user, "is_authenticated", False) else None,
		)
		data = {
			"receipt_id": result.receipt_id,
			"erp_status": result.erp_status,
			"erp_reference": result.erp_reference,
			"message": result.message,
		}
		if result.error:
			data["error"] = result.error
		return Response(data, status=status.HTTP_200_OK)


class ERPSyncProductsAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = SyncProductsSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		summary = sync_products_from_erp(
			create_missing=serializer.validated_data.get("create_missing", False),
			user=request.user if getattr(request.user, "is_authenticated", False) else None,
		)
		return Response(summary, status=status.HTTP_200_OK)


class ERPSyncLogsListAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		qs = ERPSyncLog.objects.all()[:200]
		out = ERPSyncLogSerializer(qs, many=True)
		return Response(out.data, status=status.HTTP_200_OK)


class ERPReceiptMappingsListAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		qs = ERPReceiptMapping.objects.select_related("receipt").all()[:200]
		out = ERPReceiptMappingSerializer(qs, many=True)
		return Response(out.data, status=status.HTTP_200_OK)


class ERPProductMappingsListAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		qs = ERPProductMapping.objects.select_related("product").all()[:200]
		out = ERPProductMappingSerializer(qs, many=True)
		return Response(out.data, status=status.HTTP_200_OK)
