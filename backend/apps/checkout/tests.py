from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.catalog.models import Category, Product, ProductBarcode


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
