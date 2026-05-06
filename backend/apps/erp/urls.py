from django.urls import path

from apps.erp.views import (
	ERPProductMappingsListAPIView,
	ERPReceiptMappingsListAPIView,
	ERPPushReceiptAPIView,
	ERPReceiptPayloadPreviewAPIView,
	ERPRetryReceiptAPIView,
	ERPSyncLogsListAPIView,
	ERPSyncProductsAPIView,
)

urlpatterns = [
	path("push-receipt/<int:receipt_id>/", ERPPushReceiptAPIView.as_view(), name="erp-push-receipt"),
	path(
		"retry-receipt/<int:receipt_id>/",
		ERPRetryReceiptAPIView.as_view(),
		name="erp-retry-receipt",
	),
	path("sync-products/", ERPSyncProductsAPIView.as_view(), name="erp-sync-products"),
	path("sync-logs/", ERPSyncLogsListAPIView.as_view(), name="erp-sync-logs"),
	path(
		"receipt-mappings/",
		ERPReceiptMappingsListAPIView.as_view(),
		name="erp-receipt-mappings",
	),
	path(
		"product-mappings/",
		ERPProductMappingsListAPIView.as_view(),
		name="erp-product-mappings",
	),
	path(
		"receipt-payload-preview/<int:receipt_id>/",
		ERPReceiptPayloadPreviewAPIView.as_view(),
		name="erp-receipt-payload-preview",
	),
]
