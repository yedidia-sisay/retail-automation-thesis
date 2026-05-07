from django.urls import path

from apps.audit.views import (
	CorrectionsCSVExportAPIView,
	DashboardBarcodeFallbackAPIView,
	DashboardCorrectionsAPIView,
	DashboardDetectionsAPIView,
	DashboardERPSyncAPIView,
	DashboardItemSourcesAPIView,
	DashboardPaymentsAPIView,
	DashboardReceiptCorrectnessAPIView,
	DashboardSummaryAPIView,
	DashboardTransactionsAPIView,
	DetectionsCSVExportAPIView,
	ReceiptEvaluationDetailAPIView,
	ReceiptEvaluationListCreateAPIView,
	ReceiptEvaluationsCSVExportAPIView,
	TransactionsAPIView,
	TransactionsCSVExportAPIView,
)

urlpatterns = [
	# Receipt evaluation CRUD
	path("receipt-evaluations/", ReceiptEvaluationListCreateAPIView.as_view(), name="audit-receipt-evaluation-list"),
	path("receipt-evaluations/<int:pk>/", ReceiptEvaluationDetailAPIView.as_view(), name="audit-receipt-evaluation-detail"),

	# Dashboard summaries
	path("dashboard/summary/", DashboardSummaryAPIView.as_view(), name="audit-dashboard-summary"),
	path("dashboard/transactions/", DashboardTransactionsAPIView.as_view(), name="audit-dashboard-transactions"),
	path("dashboard/item-sources/", DashboardItemSourcesAPIView.as_view(), name="audit-dashboard-item-sources"),
	path("dashboard/corrections/", DashboardCorrectionsAPIView.as_view(), name="audit-dashboard-corrections"),
	path("dashboard/barcode-fallback/", DashboardBarcodeFallbackAPIView.as_view(), name="audit-dashboard-barcode-fallback"),
	path("dashboard/detections/", DashboardDetectionsAPIView.as_view(), name="audit-dashboard-detections"),
	path("dashboard/receipt-correctness/", DashboardReceiptCorrectnessAPIView.as_view(), name="audit-dashboard-receipt-correctness"),
	path("dashboard/payments/", DashboardPaymentsAPIView.as_view(), name="audit-dashboard-payments"),
	path("dashboard/erp-sync/", DashboardERPSyncAPIView.as_view(), name="audit-dashboard-erp-sync"),

	# Transaction history
	path("transactions/", TransactionsAPIView.as_view(), name="audit-transactions"),

	# Exports
	path("export/transactions.csv", TransactionsCSVExportAPIView.as_view(), name="audit-export-transactions-csv"),
	path("export/corrections.csv", CorrectionsCSVExportAPIView.as_view(), name="audit-export-corrections-csv"),
	path("export/detections.csv", DetectionsCSVExportAPIView.as_view(), name="audit-export-detections-csv"),
	path("export/receipt-evaluations.csv", ReceiptEvaluationsCSVExportAPIView.as_view(), name="audit-export-receipt-evaluations-csv"),
]
