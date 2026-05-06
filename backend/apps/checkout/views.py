from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.checkout.serializers import (
	AcceptCheckoutItemSerializer,
	AddManualItemSerializer,
	AddBarcodeItemSerializer,
	ChangeCheckoutItemQuantitySerializer,
	CheckoutCorrectionSerializer,
	CheckoutItemSerializer,
	CheckoutSessionSerializer,
	CreateCheckoutSessionSerializer,
	RejectCheckoutItemSerializer,
	ReplaceCheckoutItemProductSerializer,
	UpdateItemQuantitySerializer,
)
from apps.checkout.services import (
	CheckoutError,
	accept_checkout_item,
	add_manual_item,
	add_barcode_item_to_checkout,
	change_checkout_item_quantity,
	cancel_checkout_session,
	create_checkout_session,
	reject_checkout_item,
	remove_item,
	replace_checkout_item_product,
	update_item_quantity,
)
from apps.receipts.serializers import ReceiptSerializer
from apps.receipts.services import create_receipt_from_checkout
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound

from apps.weighted_items.serializers import AddWeightedItemSerializer, WeightedItemEntrySerializer
from apps.weighted_items.services import add_weighted_item_to_checkout


class CheckoutSessionViewSet(viewsets.ModelViewSet):
	permission_classes = [AllowAny]
	serializer_class = CheckoutSessionSerializer

	def get_queryset(self):
		return (
			CheckoutSession.objects.select_related("cashier", "receipt")
			.prefetch_related(
				"items",
				"items__product",
				"items__weighted_entry",
				"items__weighted_entry__product",
			)
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
			if isinstance(exc.detail, dict):
				return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
			return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)

		out = ReceiptSerializer(receipt, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["get"], url_path="corrections")
	def corrections(self, request, pk=None):
		session = self.get_object()
		qs = (
			session.corrections.select_related("checkout_item", "corrected_by")
			.order_by("-created_at")
		)
		out = CheckoutCorrectionSerializer(qs, many=True, context=self.get_serializer_context())
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
			item = update_item_quantity(
				item=item,
				quantity=serializer.validated_data["quantity"],
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["patch"], url_path="change-quantity")
	def change_quantity(self, request, pk=None):
		item = self.get_object()
		serializer = ChangeCheckoutItemQuantitySerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = change_checkout_item_quantity(
				item_id=item.id,
				quantity=serializer.validated_data["quantity"],
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
				note=serializer.validated_data.get("note", ""),
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="accept")
	def accept(self, request, pk=None):
		item = self.get_object()
		serializer = AcceptCheckoutItemSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = accept_checkout_item(
				item_id=item.id,
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
				note=serializer.validated_data.get("note", ""),
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="reject")
	def reject(self, request, pk=None):
		item = self.get_object()
		serializer = RejectCheckoutItemSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = reject_checkout_item(
				item_id=item.id,
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
				note=serializer.validated_data.get("note", ""),
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = CheckoutItemSerializer(item, context=self.get_serializer_context())
		return Response(out.data, status=status.HTTP_200_OK)

	@action(detail=True, methods=["post"], url_path="replace-product")
	def replace_product(self, request, pk=None):
		item = self.get_object()
		serializer = ReplaceCheckoutItemProductSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		try:
			item = replace_checkout_item_product(
				item_id=item.id,
				product_id=serializer.validated_data["product_id"],
				quantity=serializer.validated_data.get("quantity"),
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
				note=serializer.validated_data.get("note", ""),
			)
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
			if isinstance(exc.detail, dict):
				return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
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


class AddWeightedItemAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, session_id: int):
		session = get_object_or_404(CheckoutSession, pk=session_id)
		if not session.is_editable:
			return Response(
				{"detail": "Cannot add items to a confirmed or cancelled checkout session."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		serializer = AddWeightedItemSerializer(data=request.data)
		try:
			serializer.is_valid(raise_exception=True)
		except ValidationError as exc:
			# If serializer raises a non-field business error under "detail",
			# return it as a plain string (not a list) to match the API style.
			if isinstance(exc.detail, dict) and "detail" in exc.detail:
				detail_val = exc.detail.get("detail")
				if isinstance(detail_val, list) and detail_val:
					return Response(
						{"detail": str(detail_val[0])},
						status=status.HTTP_400_BAD_REQUEST,
					)
				return Response(
					{"detail": str(detail_val)},
					status=status.HTTP_400_BAD_REQUEST,
				)
			raise

		try:
			entry = add_weighted_item_to_checkout(
				checkout_session_id=session.id,
				product_id=serializer.validated_data["product_id"],
				weight=serializer.validated_data["weight"],
				weight_unit=serializer.validated_data.get("weight_unit"),
				weight_source=serializer.validated_data.get("weight_source"),
				user=request.user if getattr(request.user, "is_authenticated", False) else None,
				raw_ocr_text=serializer.validated_data.get("raw_ocr_text"),
			)
		except CheckoutError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		out = WeightedItemEntrySerializer(entry)
		return Response(out.data, status=status.HTTP_200_OK)
