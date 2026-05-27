from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.payments.serializers import PaymentSerializer, SimulatePaymentSerializer
from apps.payments.services import get_payment, simulate_payment


class SimulatePaymentAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		serializer = SimulatePaymentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		payment = simulate_payment(
			receipt_id=serializer.validated_data["receipt_id"],
			method=serializer.validated_data.get("method", "DEMO"),
			status=serializer.validated_data.get("status", "COMPLETED"),
			amount=serializer.validated_data.get("amount"),
			user=request.user if getattr(request.user, "is_authenticated", False) else None,
			provider_response=serializer.validated_data.get("provider_response"),
		)

		out = PaymentSerializer(payment)
		return Response(out.data, status=status.HTTP_201_CREATED)


class PaymentDetailAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, payment_id: int):
		payment = get_payment(payment_id=payment_id)
		out = PaymentSerializer(payment)
		return Response(out.data, status=status.HTTP_200_OK)
