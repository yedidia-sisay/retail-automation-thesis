from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.catalog.models import Category, DetectionClassMapping, Product, ProductBarcode
from apps.catalog.serializers import (
	CategorySerializer,
	DetectionClassMappingSerializer,
	ProductBarcodeSerializer,
	ProductSerializer,
)


def _truthy_query_param(value: str | None) -> bool:
	if value is None:
		return False
	return value.strip().lower() in {"1", "true", "yes", "y", "t"}


class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
	serializer_class = ProductSerializer

	def get_queryset(self):
		queryset = (
			Product.objects.select_related("category")
			.prefetch_related("barcodes", "detection_mappings")
			.all()
		)

		if not _truthy_query_param(self.request.query_params.get("include_inactive")):
			queryset = queryset.filter(is_active=True)

		return queryset

	@action(detail=False, methods=["get"], url_path="search")
	def search(self, request):
		query = (request.query_params.get("q") or "").strip()
		if not query:
			return Response(
				{"detail": "Query parameter 'q' is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		queryset = (
			self.get_queryset()
			.filter(
				Q(name__icontains=query)
				| Q(sku__icontains=query)
				| Q(category__name__icontains=query)
				| Q(barcodes__barcode__icontains=query)
				| Q(odoo_product_id__icontains=query)
			)
			.distinct()
		)

		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@action(
		detail=False,
		methods=["get"],
		url_path=r"by-barcode/(?P<barcode>[^/]+)",
	)
	def by_barcode(self, request, barcode: str | None = None):
		barcode_value = (barcode or "").strip()
		if not barcode_value:
			return Response(
				{"detail": "Barcode is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			barcode_obj = ProductBarcode.objects.select_related("product").get(
				barcode=barcode_value
			)
		except ProductBarcode.DoesNotExist:
			return Response(
				{"detail": f"No product found for barcode '{barcode_value}'."},
				status=status.HTTP_404_NOT_FOUND,
			)

		queryset = self.get_queryset()
		try:
			product = queryset.get(pk=barcode_obj.product_id)
		except Product.DoesNotExist:
			return Response(
				{
					"detail": f"No product found for barcode '{barcode_value}' with the current filters."
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		serializer = self.get_serializer(product)
		return Response(serializer.data)


class ProductBarcodeViewSet(viewsets.ModelViewSet):
	queryset = ProductBarcode.objects.select_related("product").all()
	serializer_class = ProductBarcodeSerializer


class DetectionClassMappingViewSet(viewsets.ModelViewSet):
	queryset = DetectionClassMapping.objects.select_related("product", "product__category").all()
	serializer_class = DetectionClassMappingSerializer

	@action(detail=False, methods=["get"], url_path="by-class")
	def by_class(self, request):
		class_name = (request.query_params.get("class_name") or "").strip()
		if not class_name:
			return Response(
				{"detail": "Query parameter 'class_name' is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			mapping = self.get_queryset().get(class_name=class_name, is_active=True)
		except DetectionClassMapping.DoesNotExist:
			return Response(
				{"detail": f"No active mapping found for class_name '{class_name}'."},
				status=status.HTTP_404_NOT_FOUND,
			)

		serializer = self.get_serializer(mapping)
		return Response(serializer.data)
