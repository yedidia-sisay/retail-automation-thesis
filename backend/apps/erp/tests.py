from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.erp.clients import BaseERPClient
from apps.erp.models import ERPProductMapping, ERPReceiptMapping, ERPSyncLog
from apps.receipts.models import Receipt


class _FailingERPClient(BaseERPClient):
	erp_system = "ODOO"

	def sync_products(self):
		return []

	def push_receipt(self, payload):
		raise Exception("Simulated ERP failure")

	def get_receipt_status(self, erp_reference: str):
		return {"erp_reference": erp_reference, "status": "UNKNOWN"}


class _SuccessERPClient(BaseERPClient):
	erp_system = "ODOO-DEMO"

	def __init__(self, *, reference: str = "ODOO-DEMO-000001"):
		self.reference = reference

	def sync_products(self):
		return []

	def push_receipt(self, payload):
		return {
			"success": True,
			"erp_system": self.erp_system,
			"erp_reference": self.reference,
			"message": "Receipt pushed to simulated Odoo ERP successfully.",
		}

	def get_receipt_status(self, erp_reference: str):
		return {"erp_reference": erp_reference, "status": "SYNCED"}


class _ProductsERPClient(BaseERPClient):
	erp_system = "ODOO-DEMO"

	def __init__(self, products):
		self._products = products

	def sync_products(self):
		return list(self._products)

	def push_receipt(self, payload):
		return {"success": True, "erp_reference": "ODOO-DEMO-X"}

	def get_receipt_status(self, erp_reference: str):
		return {"erp_reference": erp_reference, "status": "SYNCED"}


class ERPIntegrationSprint9Tests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.product = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("50.00"),
			is_active=True,
		)

	def _create_confirmed_receipt(self) -> int:
		res = self.client.post("/api/checkout/sessions/", {"note": "erp"}, format="json")
		self.assertEqual(res.status_code, 201)
		session_id = res.data["id"]

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product.id, "quantity": "2.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		res = self.client.post(f"/api/checkout/sessions/{session_id}/confirm/", format="json")
		self.assertEqual(res.status_code, 200)
		receipt_id = res.data["id"]
		return receipt_id

	def _pay_receipt(self, receipt_id: int):
		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "method": "DEMO", "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)

	def test_fake_client_pushes_receipt_successfully(self):
		receipt_id = self._create_confirmed_receipt()
		self._pay_receipt(receipt_id)

		# Ensure the payload can include an ERP product id.
		ERPProductMapping.objects.create(
			product=self.product,
			erp_system="ODOO",
			erp_product_id="ODOO-PROD-001",
			erp_product_name=self.product.name,
		)

		res = self.client.post(f"/api/erp/push-receipt/{receipt_id}/", format="json")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["receipt_id"], receipt_id)
		self.assertEqual(res.data["erp_status"], "SYNCED")
		self.assertTrue(res.data["erp_reference"].startswith("ODOO-DEMO-"))

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.erp_status, Receipt.ERPStatus.SYNCED)
		self.assertIsNotNone(receipt.erp_reference)
		self.assertIsNotNone(receipt.erp_synced_at)

		self.assertTrue(
			ERPReceiptMapping.objects.filter(receipt_id=receipt_id, sync_status="SYNCED").exists()
		)
		self.assertTrue(
			ERPSyncLog.objects.filter(
				object_type="RECEIPT",
				object_id=str(receipt_id),
				action="PUSH_RECEIPT",
				status="SUCCESS",
			).exists()
		)

	def test_payload_preview_returns_expected_structure(self):
		receipt_id = self._create_confirmed_receipt()
		self._pay_receipt(receipt_id)

		res = self.client.get(f"/api/erp/receipt-payload-preview/{receipt_id}/")
		self.assertEqual(res.status_code, 200)
		self.assertIn("receipt_number", res.data)
		self.assertIn("total", res.data)
		self.assertIn("payment_status", res.data)
		self.assertIn("lines", res.data)
		self.assertEqual(len(res.data["lines"]), 1)
		line = res.data["lines"][0]
		self.assertIn("quantity", line)
		self.assertIn("unit_price", line)
		self.assertIn("subtotal", line)
		self.assertIn("product_name", line)

	def test_failed_erp_push_is_handled_safely(self):
		receipt_id = self._create_confirmed_receipt()
		self._pay_receipt(receipt_id)

		with patch("apps.erp.services.get_erp_client", return_value=_FailingERPClient()):
			res = self.client.post(f"/api/erp/push-receipt/{receipt_id}/", format="json")

		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["erp_status"], "FAILED")
		self.assertIn("error", res.data)

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.erp_status, Receipt.ERPStatus.FAILED)
		# Receipt itself remains valid and paid.
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAID)

		log = ERPSyncLog.objects.filter(object_id=str(receipt_id), action="PUSH_RECEIPT").first()
		self.assertIsNotNone(log)
		self.assertEqual(log.status, "FAILED")
		self.assertIn("Simulated ERP failure", log.error_message)

	def test_retry_sync_works_after_failure(self):
		receipt_id = self._create_confirmed_receipt()
		self._pay_receipt(receipt_id)

		with patch("apps.erp.services.get_erp_client", return_value=_FailingERPClient()):
			res = self.client.post(f"/api/erp/push-receipt/{receipt_id}/", format="json")
			self.assertEqual(res.status_code, 200)
			self.assertEqual(res.data["erp_status"], "FAILED")

		with patch(
			"apps.erp.services.get_erp_client",
			return_value=_SuccessERPClient(reference="ODOO-DEMO-RETRY"),
		):
			res = self.client.post(f"/api/erp/retry-receipt/{receipt_id}/", format="json")
			self.assertEqual(res.status_code, 200)
			self.assertEqual(res.data["erp_status"], "SYNCED")
			self.assertEqual(res.data["erp_reference"], "ODOO-DEMO-RETRY")

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.erp_status, Receipt.ERPStatus.SYNCED)
		self.assertTrue(
			ERPSyncLog.objects.filter(object_id=str(receipt_id), action="RETRY_SYNC").exists()
		)

	def test_product_sync_creates_or_updates_mappings(self):
		products = [
			{
				"erp_product_id": "ODOO-PROD-001",
				"sku": self.product.sku,
				"name": "Coca Cola 500ml",
				"barcode": "5449000000996",
				"unit_type": "PIECE",
				"current_price": "999.99",
			},
			{
				"erp_product_id": "ODOO-PROD-UNKNOWN",
				"sku": "DOES-NOT-EXIST",
				"name": "Not in local catalog",
				"barcode": "0000000000000",
				"unit_type": "PIECE",
				"current_price": "10.00",
			},
		]

		original_name = self.product.name
		original_price = self.product.current_price

		with patch("apps.erp.services.get_erp_client", return_value=_ProductsERPClient(products)):
			res = self.client.post(
				"/api/erp/sync-products/",
				{"create_missing": False},
				format="json",
			)
			self.assertEqual(res.status_code, 200)
			self.assertEqual(res.data["skipped_count"], 1)

		self.product.refresh_from_db()
		self.assertEqual(self.product.name, original_name)
		self.assertEqual(self.product.current_price, original_price)
		self.assertEqual(self.product.odoo_product_id, "ODOO-PROD-001")

		self.assertTrue(
			ERPProductMapping.objects.filter(product=self.product, erp_product_id="ODOO-PROD-001").exists()
		)

	def test_product_sync_create_missing_false_does_not_create_products(self):
		products = [
			{
				"erp_product_id": "ODOO-PROD-NEW",
				"sku": "NEW-SKU",
				"name": "New Product",
				"barcode": "1111111111111",
				"unit_type": "PIECE",
				"current_price": "10.00",
			}
		]
		count_before = Product.objects.count()
		with patch("apps.erp.services.get_erp_client", return_value=_ProductsERPClient(products)):
			res = self.client.post(
				"/api/erp/sync-products/",
				{"create_missing": False},
				format="json",
			)
			self.assertEqual(res.status_code, 200)
			self.assertEqual(Product.objects.count(), count_before)
			self.assertEqual(res.data["skipped_count"], 1)

	def test_product_sync_create_missing_true_can_create_products(self):
		products = [
			{
				"erp_product_id": "ODOO-PROD-NEW",
				"sku": "NEW-SKU",
				"name": "New Product",
				"barcode": "1111111111111",
				"unit_type": "PIECE",
				"current_price": "10.00",
			}
		]
		with patch("apps.erp.services.get_erp_client", return_value=_ProductsERPClient(products)):
			res = self.client.post(
				"/api/erp/sync-products/",
				{"create_missing": True},
				format="json",
			)
			self.assertEqual(res.status_code, 200)
			self.assertGreaterEqual(res.data["created_count"], 1)

		self.assertTrue(Product.objects.filter(sku="NEW-SKU").exists())
		new_product = Product.objects.get(sku="NEW-SKU")
		self.assertTrue(
			ERPProductMapping.objects.filter(product=new_product, erp_product_id="ODOO-PROD-NEW").exists()
		)
