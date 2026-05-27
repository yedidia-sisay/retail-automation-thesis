from django.urls import path

from apps.receipts.views import ReceiptDetailAPIView, ReceiptPaymentsAPIView, ReceiptPrintPreviewAPIView

urlpatterns = [
	path("<int:receipt_id>/", ReceiptDetailAPIView.as_view(), name="receipt-detail"),
	path(
		"<int:receipt_id>/payments/",
		ReceiptPaymentsAPIView.as_view(),
		name="receipt-payments",
	),
	path(
		"<int:receipt_id>/print-preview/",
		ReceiptPrintPreviewAPIView.as_view(),
		name="receipt-print-preview",
	),
]
