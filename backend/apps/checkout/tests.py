from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.catalog.models import Category, Product, ProductBarcode
from apps.checkout.models import CheckoutCorrection, CheckoutItem, CheckoutSession
from apps.checkout.services import recalculate_checkout_totals
from apps.receipts.models import Receipt
from apps.weighted_items.models import WeightedItemEntry


class BarcodeFallbackSprint4APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.product = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)
		self.barcode_value = "5449000000996"
		ProductBarcode.objects.create(
			product=self.product,
			barcode=self.barcode_value,
			is_primary=True,
		)

	def test_known_barcode_adds_item_and_updates_totals(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "b"}, format="json")
		self.assertEqual(res.status_code, 201)
		session_id = res.data["id"]

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": 1},
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_amount"], "35.00")
		self.assertEqual(len(res.data["items"]), 1)
		self.assertEqual(res.data["items"][0]["source"], "BARCODE")
		self.assertEqual(res.data["items"][0]["quantity"], "1.000")
		self.assertTrue(
			AuditEvent.objects.filter(event_type="BARCODE_FALLBACK_SUCCESS").exists()
		)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": 3},
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_amount"], "140.00")
		self.assertEqual(len(res.data["items"]), 1)
		self.assertEqual(res.data["items"][0]["quantity"], "4.000")

	def test_unknown_barcode_returns_404_and_logs_audit(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "b"}, format="json")
		session_id = res.data["id"]

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": "0000000000000", "quantity": 1},
			format="json",
		)
		self.assertEqual(res.status_code, 404)
		self.assertIn("detail", res.data)
		self.assertTrue(
			AuditEvent.objects.filter(event_type="BARCODE_FALLBACK_UNKNOWN").exists()
		)

	def test_confirmed_session_cannot_add_barcode_items(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "b"}, format="json")
		session_id = res.data["id"]
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": 1},
			format="json",
		)

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": 1},
			format="json",
		)
		self.assertEqual(res.status_code, 400)

	def test_barcode_item_appears_on_receipt_after_confirmation(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "b"}, format="json")
		session_id = res.data["id"]
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": 2},
			format="json",
		)

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)
		receipt_id = res.data["id"]
		self.assertEqual(len(res.data["lines"]), 1)
		self.assertEqual(res.data["lines"][0]["product_sku"], "COCA-500")

		res = self.client.get(f"/api/receipts/{receipt_id}/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(len(res.data["lines"]), 1)
		self.assertEqual(res.data["total"], "70.00")


class CashierReviewSprint6APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.product_a = Product.objects.create(
			category=self.category,
			name="Pepsi 500ml",
			sku="PEPSI-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("30.00"),
			is_active=True,
		)
		self.product_b = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)

	def _create_session(self) -> CheckoutSession:
		res = self.client.post("/api/checkout/sessions/", {"note": "s6"}, format="json")
		self.assertEqual(res.status_code, 201)
		return CheckoutSession.objects.get(pk=res.data["id"])

	def test_cashier_can_accept_needs_review_item_and_log_correction(self):
		session = self._create_session()
		item = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_a,
			quantity=Decimal("1.000"),
			unit_price=self.product_a.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
			confidence=Decimal("0.5500"),
		)
		recalculate_checkout_totals(session)

		res = self.client.post(
			f"/api/checkout/items/{item.id}/accept/",
			{"note": "Correct detection"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		item.refresh_from_db()
		self.assertEqual(item.review_status, CheckoutItem.ReviewStatus.ACCEPTED)
		self.assertEqual(item.status, CheckoutItem.Status.ACTIVE)
		self.assertTrue(
			CheckoutCorrection.objects.filter(
				checkout_item=item,
				correction_type=CheckoutCorrection.CorrectionType.ACCEPT_ITEM,
			).exists()
		)

	def test_cashier_can_reject_item_and_it_no_longer_affects_total(self):
		session = self._create_session()
		manual = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_b,
			quantity=Decimal("1.000"),
			unit_price=self.product_b.current_price,
			source=CheckoutItem.Source.MANUAL,
			status=CheckoutItem.Status.ACTIVE,
			review_status=CheckoutItem.ReviewStatus.NOT_REQUIRED,
		)
		vision = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_a,
			quantity=Decimal("1.000"),
			unit_price=self.product_a.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
			confidence=Decimal("0.5200"),
		)
		recalculate_checkout_totals(session)
		session.refresh_from_db()
		self.assertEqual(session.total_amount, Decimal("65.00"))

		res = self.client.post(
			f"/api/checkout/items/{vision.id}/reject/",
			{"note": "Wrong YOLO detection"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		vision.refresh_from_db()
		session.refresh_from_db()
		self.assertEqual(vision.review_status, CheckoutItem.ReviewStatus.REJECTED)
		self.assertEqual(vision.status, CheckoutItem.Status.REMOVED)
		self.assertEqual(session.total_amount, manual.subtotal)
		self.assertTrue(
			CheckoutCorrection.objects.filter(
				checkout_item=vision,
				correction_type=CheckoutCorrection.CorrectionType.REJECT_ITEM,
			).exists()
		)

	def test_cashier_can_replace_wrong_product(self):
		session = self._create_session()
		item = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_a,
			quantity=Decimal("1.000"),
			unit_price=self.product_a.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
			confidence=Decimal("0.6000"),
		)
		recalculate_checkout_totals(session)

		res = self.client.post(
			f"/api/checkout/items/{item.id}/replace-product/",
			{"product_id": self.product_b.id, "quantity": "2.000", "note": "Was Coca Cola"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		item.refresh_from_db()
		self.assertEqual(item.product_id, self.product_b.id)
		self.assertEqual(item.unit_price, self.product_b.current_price)
		self.assertEqual(item.quantity, Decimal("2.000"))
		self.assertEqual(item.subtotal, Decimal("70.00"))
		self.assertEqual(item.review_status, CheckoutItem.ReviewStatus.REPLACED)
		self.assertTrue(
			CheckoutCorrection.objects.filter(
				checkout_item=item,
				correction_type=CheckoutCorrection.CorrectionType.REPLACE_PRODUCT,
			).exists()
		)

		log = CheckoutCorrection.objects.filter(checkout_item=item).order_by("-created_at").first()
		self.assertIsNotNone(log)
		self.assertEqual(log.before_data["product_id"], self.product_a.id)
		self.assertEqual(log.after_data["product_id"], self.product_b.id)

	def test_cashier_can_change_quantity_and_subtotals_update(self):
		session = self._create_session()
		item = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_b,
			quantity=Decimal("1.000"),
			unit_price=self.product_b.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
		)
		recalculate_checkout_totals(session)

		res = self.client.patch(
			f"/api/checkout/items/{item.id}/change-quantity/",
			{"quantity": "3.000", "note": "Counted three bottles"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		item.refresh_from_db()
		session.refresh_from_db()
		self.assertEqual(item.quantity, Decimal("3.000"))
		self.assertEqual(item.subtotal, Decimal("105.00"))
		self.assertEqual(session.total_amount, Decimal("105.00"))
		self.assertEqual(item.review_status, CheckoutItem.ReviewStatus.ACCEPTED)
		self.assertTrue(
			CheckoutCorrection.objects.filter(
				checkout_item=item,
				correction_type=CheckoutCorrection.CorrectionType.CHANGE_QUANTITY,
			).exists()
		)

	def test_checkout_cannot_be_confirmed_with_unresolved_needs_review_item(self):
		session = self._create_session()
		CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_a,
			quantity=Decimal("1.000"),
			unit_price=self.product_a.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
		)
		recalculate_checkout_totals(session)

		res = self.client.post(f"/api/checkout/sessions/{session.id}/confirm/", format="json")
		self.assertEqual(res.status_code, 400)
		self.assertIn("detail", res.data)
		self.assertIn("unresolved_items", res.data)
		self.assertEqual(Receipt.objects.count(), 0)

	def test_checkout_can_be_confirmed_after_all_risky_items_resolved(self):
		session = self._create_session()
		item = CheckoutItem.objects.create(
			checkout_session=session,
			product=self.product_a,
			quantity=Decimal("1.000"),
			unit_price=self.product_a.current_price,
			source=CheckoutItem.Source.VISION,
			status=CheckoutItem.Status.NEEDS_REVIEW,
			review_status=CheckoutItem.ReviewStatus.NEEDS_REVIEW,
		)
		recalculate_checkout_totals(session)
		self.client.post(
			f"/api/checkout/items/{item.id}/accept/",
			{"note": "ok"},
			format="json",
		)

		res = self.client.post(f"/api/checkout/sessions/{session.id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)
		self.assertIn("receipt_number", res.data)
		self.assertEqual(len(res.data["lines"]), 1)
		self.assertEqual(res.data["total"], "30.00")


class WeightedItemsSprint7APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Produce", slug="produce")
		self.mango = Product.objects.create(
			category=self.category,
			name="Mango",
			sku="MANGO-KG",
			unit_type=Product.UnitType.KG,
			current_price=Decimal("120.00"),
			is_active=True,
		)
		self.cola = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)

	def _create_session_id(self) -> int:
		res = self.client.post("/api/checkout/sessions/", {"note": "s7"}, format="json")
		self.assertEqual(res.status_code, 201)
		return res.data["id"]

	def test_cashier_can_add_weighted_product_manually_and_totals_update(self):
		session_id = self._create_session_id()

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{
				"product_id": self.mango.id,
				"weight": "1.25",
				"weight_unit": "KG",
				"weight_source": "MANUAL",
			},
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["product"], self.mango.id)
		self.assertEqual(res.data["product_name"], "Mango")
		self.assertEqual(res.data["weight"], "1.250")
		self.assertEqual(res.data["unit_price"], "120.00")
		self.assertEqual(res.data["subtotal"], "150.00")
		self.assertEqual(res.data["weight_source"], "MANUAL")

		self.assertEqual(WeightedItemEntry.objects.count(), 1)
		entry = WeightedItemEntry.objects.select_related("checkout_item").get(pk=res.data["id"])
		self.assertIsNotNone(entry.checkout_item_id)
		item = entry.checkout_item
		self.assertEqual(item.source, CheckoutItem.Source.WEIGHTED)
		self.assertEqual(item.quantity, Decimal("1.250"))
		self.assertEqual(item.unit_price, Decimal("120.00"))
		self.assertEqual(item.subtotal, Decimal("150.00"))

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertEqual(session.total_amount, Decimal("150.00"))

	def test_backend_rejects_piece_product_in_weighted_workflow(self):
		session_id = self._create_session_id()

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.cola.id, "weight": "1.25", "weight_unit": "KG"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertEqual(res.data["detail"], "This product is not sold by weight.")
		self.assertEqual(WeightedItemEntry.objects.count(), 0)
		self.assertEqual(CheckoutItem.objects.filter(checkout_session_id=session_id).count(), 0)

	def test_backend_rejects_zero_weight(self):
		session_id = self._create_session_id()
		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "0", "weight_unit": "KG"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertIn("weight", res.data)
		self.assertEqual(res.data["weight"], ["Weight must be greater than zero."])

	def test_backend_rejects_negative_weight(self):
		session_id = self._create_session_id()
		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "-1.0", "weight_unit": "KG"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertIn("weight", res.data)

	def test_weighted_item_appears_in_checkout_session_detail(self):
		session_id = self._create_session_id()
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "1.25", "weight_unit": "KG"},
			format="json",
		)

		res = self.client.get(f"/api/checkout/sessions/{session_id}/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total_amount"], "150.00")
		self.assertEqual(len(res.data["items"]), 1)
		item = res.data["items"][0]
		self.assertEqual(item["source"], "WEIGHTED")
		self.assertEqual(item["product_name"], "Mango")
		self.assertEqual(item["quantity"], "1.250")
		self.assertEqual(item["subtotal"], "150.00")
		self.assertIsNotNone(item.get("weighted_entry"))
		self.assertEqual(item["weighted_entry"]["weight"], "1.250")

	def test_weighted_item_appears_on_receipt_after_checkout_confirmation(self):
		session_id = self._create_session_id()
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "1.25", "weight_unit": "KG"},
			format="json",
		)

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["total"], "150.00")
		self.assertEqual(len(res.data["lines"]), 1)
		line = res.data["lines"][0]
		self.assertEqual(line["product_name"], "Mango")
		self.assertEqual(line["quantity"], "1.250")
		self.assertEqual(line["unit_price"], "120.00")
		self.assertEqual(line["subtotal"], "150.00")
		self.assertEqual(line["source"], "WEIGHTED")

	def test_cannot_add_weighted_item_to_confirmed_or_cancelled_session(self):
		session_id = self._create_session_id()
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "1.25", "weight_unit": "KG"},
			format="json",
		)

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "1.00", "weight_unit": "KG"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertIn("detail", res.data)

		session_id = self._create_session_id()
		res = self.client.post(f"/api/checkout/sessions/{session_id}/cancel/", format="json")
		self.assertEqual(res.status_code, 200)
		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{"product_id": self.mango.id, "weight": "1.00", "weight_unit": "KG"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertIn("detail", res.data)

	def test_ocr_placeholder_is_stored_but_no_ocr_is_run(self):
		session_id = self._create_session_id()
		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-weighted-item/",
			{
				"product_id": self.mango.id,
				"weight": "1.25",
				"weight_unit": "KG",
				"weight_source": "OCR",
				"raw_ocr_text": "1.25 kg",
			},
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		entry = WeightedItemEntry.objects.get(pk=res.data["id"])
		self.assertEqual(entry.weight_source, "OCR")
		self.assertEqual(entry.raw_ocr_text, "1.25 kg")
