from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.checkout.serializers import (
	AddManualItemSerializer,
	AddBarcodeItemSerializer,
	CheckoutItemSerializer,
	CheckoutSessionSerializer,
	CreateCheckoutSessionSerializer,
	UpdateItemQuantitySerializer,
)
from apps.checkout.services import (
	CheckoutError,
	add_manual_item,
	add_barcode_item_to_checkout,
	cancel_checkout_session,
	create_checkout_session,
	remove_item,
	update_item_quantity,
)
from apps.receipts.serializers import ReceiptSerializer
from apps.receipts.services import create_receipt_from_checkout
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound


class CheckoutSessionViewSet(viewsets.ModelViewSet):
	permission_classes = [AllowAny]
	serializer_class = CheckoutSessionSerializer

	def get_queryset(self):
		return (
			CheckoutSession.objects.select_related("cashier")
			.prefetch_related("items", "items__product")
			.all()
		)

	def create(self, request, *args, **kwargs):
		serializer = CreateCheckoutSessionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		note = serializer.validated_data.get("note", "")
		cashier = request.user if getattr(request.user, "is_authenticated", False) else None

		session = create_checkout_session(cashier=cashier, note=note)
		out = CheckoutSessionSerializer(session, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=["post"], url_path="add-manual-item")
	def add_manual_item_action(self, request, pk=None):
		session = self.get_object()
		serializer = AddManualItemSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = add_manual_item(
				session=session,
				product_id=serializer.validated_data["product_id"],
				quantity=serializer.validated_data["quantity"],
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="confirm")
	def confirm(self, request, pk=None):
		session = self.get_object()
		try:
			receipt = create_receipt_from_checkout(session)
		except ValidationError as exc:
			return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

		out = ReceiptSerializer(receipt, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="cancel")
	def cancel(self, request, pk=None):
		session = self.get_object()
		try:
			session = cancel_checkout_session(session)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutSessionSerializer(session, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)


class CheckoutItemViewSet(viewsets.ReadOnlyModelViewSet):
	permission_classes = [AllowAny]
	serializer_class = CheckoutItemSerializer

	def get_queryset(self):
		return CheckoutItem.objects.select_related("checkout_session", "product").all()

	@action(detail=True, methods=["patch"], url_path="update-quantity")
	def update_quantity(self, request, pk=None):
		item = self.get_object()
		serializer = UpdateItemQuantitySerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = update_item_quantity(item=item, quantity=serializer.validated_data["quantity"])
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="remove")
	def remove(self, request, pk=None):
		item = self.get_object()
		try:
			item = remove_item(item)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)


class ConfirmCheckoutAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, session_id: int):
		session = get_object_or_404(CheckoutSession, pk=session_id)
		try:
			receipt = create_receipt_from_checkout(session)
		except ValidationError as exc:
			return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = ReceiptSerializer(receipt)
		return Response(out.data, status=status.HTTP_200_OK)


class AddBarcodeItemAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, session_id: int):
		session = get_object_or_404(CheckoutSession, pk=session_id)
		if not session.is_editable:
			return Response(
				{"detail": "Cannot add items to a confirmed or cancelled checkout session."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		serializer = AddBarcodeItemSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			session = add_barcode_item_to_checkout(
				session=session,
				barcode=serializer.validated_data["barcode"],
				quantity=serializer.validated_data.get("quantity"),
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
			)
		except NotFound as exc:
			return Response({"detail": str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)
		except ValidationError as exc:
			return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		session = (
			CheckoutSession.objects.select_related("cashier")
			.prefetch_related("items", "items__product")
			.get(pk=session.pk)
		)
		out = CheckoutSessionSerializer(session)
		return Response(out.data, status=status.HTTP_200_OK)
