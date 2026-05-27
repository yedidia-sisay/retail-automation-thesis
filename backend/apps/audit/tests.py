from __future__ import annotations

from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession
from apps.checkout.services import recalculate_checkout_totals
from apps.erp.models import ERPSyncLog
from apps.payments.services import simulate_payment
from apps.receipts.models import Receipt
from apps.receipts.services import create_receipt_from_checkout
from apps.vision.models import DetectedObject, DetectionRun, ModelVersion


class AuditSprint10APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.p1 = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)
		self.p2 = Product.objects.create(
			category=self.category,
			name="Sprite 500ml",
			sku="SPR-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("30.00"),
			is_active=True,
		)
		self.p3 = Product.objects.create(
			category=self.category,
			name="Fanta 500ml",
			sku="FAN-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("25.00"),
			is_active=True,
		)
		self.p4 = Product.objects.create(
			category=self.category,
			name="Apple (kg)",
			sku="APL-KG",
			unit_type=Product.UnitType.KG,
			current_price=Decimal("120.00"),
			is_active=True,
		)

		# Session 1: completed + paid
		self.session1 = CheckoutSession.objects.create(status=CheckoutSession.Status.OPEN)
		CheckoutItem.objects.create(
			checkout_session=self.session1,
			product=self.p1,
			quantity=Decimal("1.000"),
			unit_price=self.p1.current_price,
			source=CheckoutItem.Source.MANUAL,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
		)
		CheckoutItem.objects.create(
			checkout_session=self.session1,
			product=self.p2,
			quantity=Decimal("1.000"),
			unit_price=self.p2.current_price,
			source=CheckoutItem.Source.BARCODE,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
		)
		vision_item = CheckoutItem.objects.create(
			checkout_session=self.session1,
			product=self.p3,
			quantity=Decimal("1.000"),
			unit_price=self.p3.current_price,
			confidence=Decimal("0.9000"),
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.ACCEPTED,
		)
		CheckoutItem.objects.create(
			checkout_session=self.session1,
			product=self.p4,
			quantity=Decimal("0.500"),
			unit_price=self.p4.current_price,
			source=CheckoutItem.Source.WEIGHTED,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
		)
		recalculate_checkout_totals(self.session1)

		# Create a receipt (also sets confirmed_at)
		self.receipt1 = create_receipt_from_checkout(self.session1)
		# Mark paid (sets session completed + completed_at)
		simulate_payment(receipt_id=self.receipt1.id, status="COMPLETED")
		self.session1.refresh_from_db()

		# Some corrections (one per type)
		CheckoutCorrection.objects.create(
			checkout_session=self.session1,
			checkout_item=vision_item,
			correction_type=CheckoutCorrection.CorrectionType.ACCEPT_ITEM,
			before_data={"review_status": "NEEDS_REVIEW"},
			after_data={"review_status": "ACCEPTED"},
		)
		CheckoutCorrection.objects.create(
			checkout_session=self.session1,
			checkout_item=vision_item,
			correction_type=CheckoutCorrection.CorrectionType.REJECT_ITEM,
			before_data={"review_status": "NEEDS_REVIEW"},
			after_data={"review_status": "REJECTED"},
		)
		CheckoutCorrection.objects.create(
			checkout_session=self.session1,
			checkout_item=vision_item,
			correction_type=CheckoutCorrection.CorrectionType.REPLACE_PRODUCT,
			before_data={"product_sku": "FAN-500"},
			after_data={"product_sku": "SPR-500"},
		)
		CheckoutCorrection.objects.create(
			checkout_session=self.session1,
			checkout_item=vision_item,
			correction_type=CheckoutCorrection.CorrectionType.CHANGE_QUANTITY,
			before_data={"quantity": "1.000"},
			after_data={"quantity": "2.000"},
		)

		# Detection run + objects
		mv = ModelVersion.objects.create(name="yolo", version="v1", is_active=True)
		image = SimpleUploadedFile("frame.jpg", b"fake-image", content_type="image/jpeg")
		run = DetectionRun.objects.create(
			checkout_session=self.session1,
			image=image,
			model_version=mv,
			status=DetectionRun.Status.COMPLETED,
			raw_output={"detections": []},
		)
		DetectedObject.objects.create(
			detection_run=run,
			class_name="coca_cola_500ml",
			confidence=Decimal("0.9000"),
			bbox_x1=Decimal("0.00"),
			bbox_y1=Decimal("0.00"),
			bbox_x2=Decimal("1.00"),
			bbox_y2=Decimal("1.00"),
			matched_product=self.p1,
			review_status=DetectedObject.ReviewStatus.AUTO_ACCEPTED,
		)
		DetectedObject.objects.create(
			detection_run=run,
			class_name="sprite_500ml",
			confidence=Decimal("0.7000"),
			bbox_x1=Decimal("0.00"),
			bbox_y1=Decimal("0.00"),
			bbox_x2=Decimal("1.00"),
			bbox_y2=Decimal("1.00"),
			matched_product=self.p2,
			review_status=DetectedObject.ReviewStatus.NEEDS_REVIEW,
		)
		DetectedObject.objects.create(
			detection_run=run,
			class_name="unknown",
			confidence=Decimal("0.1000"),
			bbox_x1=Decimal("0.00"),
			bbox_y1=Decimal("0.00"),
			bbox_x2=Decimal("1.00"),
			bbox_y2=Decimal("1.00"),
			matched_product=None,
			review_status=DetectedObject.ReviewStatus.UNKNOWN_CLASS,
		)
		DetectedObject.objects.create(
			detection_run=run,
			class_name="low_conf",
			confidence=Decimal("0.3000"),
			bbox_x1=Decimal("0.00"),
			bbox_y1=Decimal("0.00"),
			bbox_x2=Decimal("1.00"),
			bbox_y2=Decimal("1.00"),
			matched_product=self.p3,
			review_status=DetectedObject.ReviewStatus.REJECTED_LOW_CONFIDENCE,
		)

		# ERP logs (for completeness)
		ERPSyncLog.objects.create(
			object_type=ERPSyncLog.ObjectType.RECEIPT,
			object_id=str(self.receipt1.id),
			action=ERPSyncLog.Action.PUSH_RECEIPT,
			status=ERPSyncLog.Status.SUCCESS,
			request_payload={},
			response_payload={},
		)
		ERPSyncLog.objects.create(
			object_type=ERPSyncLog.ObjectType.RECEIPT,
			object_id=str(self.receipt1.id),
			action=ERPSyncLog.Action.RETRY_SYNC,
			status=ERPSyncLog.Status.FAILED,
			request_payload={},
			response_payload={},
			error_message="fail",
		)

		# Session 2: cancelled
		self.session2 = CheckoutSession.objects.create(status=CheckoutSession.Status.OPEN)
		self.session2.cancel()

	def test_dashboard_summary_returns_transaction_counts(self):
		res = self.client.get("/api/audit/dashboard/summary/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_sessions"], 2)
		self.assertEqual(res.data["completed_sessions"], 1)
		self.assertEqual(res.data["cancelled_sessions"], 1)
		self.assertEqual(res.data["paid_sessions"], 1)
		self.assertEqual(res.data["total_revenue"], str(self.receipt1.total))

	def test_item_source_breakdown_works(self):
		res = self.client.get("/api/audit/dashboard/item-sources/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["MANUAL"], 1)
		self.assertEqual(res.data["BARCODE"], 1)
		self.assertEqual(res.data["VISION"], 1)
		self.assertEqual(res.data["WEIGHTED"], 1)

	def test_correction_summary_works(self):
		res = self.client.get("/api/audit/dashboard/corrections/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_corrections"], 4)
		self.assertEqual(res.data["accepted_count"], 1)
		self.assertEqual(res.data["rejected_count"], 1)
		self.assertEqual(res.data["replaced_count"], 1)
		self.assertEqual(res.data["quantity_changed_count"], 1)

	def test_barcode_fallback_summary_works(self):
		res = self.client.get("/api/audit/dashboard/barcode-fallback/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["barcode_item_count"], 1)
		self.assertEqual(res.data["sessions_using_barcode"], 1)

	def test_detection_review_summary_works(self):
		res = self.client.get("/api/audit/dashboard/detections/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_detection_runs"], 1)
		self.assertEqual(res.data["total_detected_objects"], 4)
		self.assertEqual(res.data["auto_accepted_count"], 1)
		self.assertEqual(res.data["needs_review_count"], 1)
		self.assertEqual(res.data["rejected_count"], 1)
		self.assertEqual(res.data["unknown_count"], 1)

	def test_receipt_evaluation_can_be_created_and_affects_summary(self):
		res = self.client.post(
			"/api/audit/receipt-evaluations/",
			{
				"receipt": self.receipt1.id,
				"is_correct": True,
				"product_names_correct": True,
				"quantities_correct": True,
				"prices_correct": True,
				"subtotals_correct": True,
				"total_correct": True,
				"notes": "ok",
			},
			format="json",
		)
		self.assertEqual(res.status_code, 201)

		res = self.client.get("/api/audit/dashboard/receipt-correctness/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_receipts"], Receipt.objects.count())
		self.assertEqual(res.data["receipts_marked_correct"], 1)

	def test_transaction_history_endpoint_returns_expected_fields(self):
		res = self.client.get("/api/audit/transactions/")
		self.assertEqual(res.status_code, 200)
		self.assertIn("results", res.data)
		self.assertEqual(len(res.data["results"]), 2)
		row = res.data["results"][0]
		for key in [
			"checkout_session_id",
			"duration_seconds",
			"total_amount",
			"vision_item_count",
			"barcode_item_count",
			"manual_item_count",
			"weighted_item_count",
			"correction_count",
			"payment_status",
			"erp_status",
		]:
			self.assertIn(key, row)

	def test_csv_transaction_export_works(self):
		res = self.client.get("/api/audit/export/transactions.csv")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res["Content-Type"], "text/csv")
		content = res.content.decode("utf-8")
		self.assertIn("checkout_session_id,cashier,status,created_at", content.splitlines()[0])
		self.assertGreaterEqual(len(content.splitlines()), 3)  # header + 2 rows

	def test_csv_correction_export_works(self):
		res = self.client.get("/api/audit/export/corrections.csv")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res["Content-Type"], "text/csv")
		content = res.content.decode("utf-8")
		self.assertIn("correction_id,checkout_session_id", content.splitlines()[0])
		self.assertGreaterEqual(len(content.splitlines()), 2)

	def test_csv_detection_export_works(self):
		res = self.client.get("/api/audit/export/detections.csv")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res["Content-Type"], "text/csv")
		content = res.content.decode("utf-8")
		self.assertIn("detection_run_id,detected_object_id", content.splitlines()[0])
		self.assertGreaterEqual(len(content.splitlines()), 5)  # header + 4 rows
