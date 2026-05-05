from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.receipts.models import Receipt


class ReceiptSprint3APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.product_1 = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)
		self.product_2 = Product.objects.create(
			category=self.category,
			name="Sprite 500ml",
			sku="SPRITE-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("30.00"),
			is_active=True,
		)

	def test_confirm_creates_receipt_and_is_idempotent(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "t"}, format="json")
		self.assertEqual(res.status_code, 201)
		session_id = res.data["id"]

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product_1.id, "quantity": "2.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product_2.id, "quantity": "1.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		item_2_id = res.data["id"]

		res = self.client.post(f"/api/checkout/items/{item_2_id}/remove/", format="json")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["status"], "REMOVED")

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)
		receipt_id = res.data["id"]
		self.assertTrue(res.data["receipt_number"].startswith("RCP-"))
		self.assertEqual(res.data["payment_status"], "UNPAID")
		self.assertEqual(len(res.data["lines"]), 1)
		self.assertEqual(res.data["lines"][0]["product_sku"], "COCA-500")
		self.assertEqual(Receipt.objects.count(), 1)

		res2 = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res2.status_code, 200)
		self.assertEqual(res2.data["id"], receipt_id)
		self.assertEqual(Receipt.objects.count(), 1)

	def test_confirm_empty_checkout_returns_400(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "empty"}, format="json")
		self.assertEqual(res.status_code, 201)
		session_id = res.data["id"]

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 400)
		self.assertIn("detail", res.data)

	def test_receipt_detail_and_print_preview(self):
		res = self.client.post("/api/checkout/sessions/", {"note": "preview"}, format="json")
		session_id = res.data["id"]
		self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product_1.id, "quantity": "1.000"},
			format="json",
		)
		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		receipt_id = res.data["id"]

		res = self.client.get(f"/api/receipts/{receipt_id}/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["id"], receipt_id)
		self.assertEqual(len(res.data["lines"]), 1)

		res = self.client.get(f"/api/receipts/{receipt_id}/print-preview/")
		self.assertEqual(res.status_code, 200)
		self.assertIn("printable_text", res.data)
		self.assertIn("TOTAL", res.data["printable_text"])
