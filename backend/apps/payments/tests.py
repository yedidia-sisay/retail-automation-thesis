from __future__ import annotations

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductBarcode
from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.payments.models import Payment
from apps.receipts.models import Receipt


class PaymentSimulationSprint8APITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Demo", slug="demo")
		self.product = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA-500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("50.00"),
			is_active=True,
		)
		self.barcode_value = "5449000000996"
		ProductBarcode.objects.create(
			product=self.product,
			barcode=self.barcode_value,
			is_primary=True,
		)

	def _create_confirmed_receipt(self) -> tuple[int, int]:
		res = self.client.post("/api/checkout/sessions/", {"note": "s8"}, format="json")
		self.assertEqual(res.status_code, 201)
		session_id = res.data["id"]

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product.id, "quantity": "5.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 200)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/confirm/",
			format="json",
		)
		self.assertEqual(res.status_code, 200)
		receipt_id = res.data["id"]
		return session_id, receipt_id

	def test_cashier_can_simulate_completed_payment(self):
		session_id, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "method": "DEMO", "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		self.assertEqual(Payment.objects.count(), 1)
		payment = Payment.objects.get(pk=res.data["id"])
		self.assertEqual(payment.status, Payment.Status.COMPLETED)
		self.assertTrue(payment.transaction_reference.startswith("SIM-"))

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAID)

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertEqual(session.status, CheckoutSession.Status.COMPLETED)

	def test_cashier_can_simulate_failed_payment(self):
		session_id, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{
				"receipt_id": receipt_id,
				"method": "DEMO",
				"status": "FAILED",
				"provider_response": {"reason": "Demo failed payment"},
			},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		payment = Payment.objects.get(pk=res.data["id"])
		self.assertEqual(payment.status, Payment.Status.FAILED)
		self.assertEqual(payment.provider_response.get("reason"), "Demo failed payment")

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAYMENT_FAILED)
		self.assertFalse(receipt.is_locked)

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertNotEqual(session.status, CheckoutSession.Status.COMPLETED)

	def test_cashier_can_simulate_cancelled_payment(self):
		session_id, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "method": "DEMO", "status": "CANCELLED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		payment = Payment.objects.get(pk=res.data["id"])
		self.assertEqual(payment.status, Payment.Status.CANCELLED)

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAYMENT_CANCELLED)
		self.assertFalse(receipt.is_locked)

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertNotEqual(session.status, CheckoutSession.Status.COMPLETED)

	def test_cashier_can_simulate_pending_payment(self):
		session_id, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "method": "DEMO", "status": "PENDING"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		payment = Payment.objects.get(pk=res.data["id"])
		self.assertEqual(payment.status, Payment.Status.PENDING)

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAYMENT_PENDING)

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertEqual(session.status, CheckoutSession.Status.PAYMENT_PENDING)

	def test_payment_amount_must_match_receipt_total(self):
		_, receipt_id = self._create_confirmed_receipt()
		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.total, Decimal("250.00"))

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "COMPLETED", "amount": "200.00"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertEqual(Payment.objects.count(), 0)

	def test_cannot_pay_an_already_paid_receipt_again(self):
		_, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		self.assertEqual(Payment.objects.count(), 1)

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)
		self.assertEqual(Payment.objects.count(), 1)

		receipt = Receipt.objects.get(pk=receipt_id)
		self.assertEqual(receipt.payment_status, Receipt.PaymentStatus.PAID)

	def test_paid_receipt_blocks_checkout_edits(self):
		session_id, receipt_id = self._create_confirmed_receipt()
		item = CheckoutItem.objects.filter(checkout_session_id=session_id).first()
		self.assertIsNotNone(item)

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-manual-item/",
			{"product_id": self.product.id, "quantity": "1.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)

		res = self.client.post(
			f"/api/checkout/sessions/{session_id}/add-barcode/",
			{"barcode": self.barcode_value, "quantity": "1.000"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)

		res = self.client.patch(
			f"/api/checkout/items/{item.id}/change-quantity/",
			{"quantity": "2.000", "note": "try edit after pay"},
			format="json",
		)
		self.assertEqual(res.status_code, 400)

	def test_failed_payment_does_not_mark_transaction_complete(self):
		session_id, receipt_id = self._create_confirmed_receipt()

		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "FAILED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)

		session = CheckoutSession.objects.get(pk=session_id)
		self.assertNotEqual(session.status, CheckoutSession.Status.COMPLETED)

	def test_payment_appears_in_receipt_payment_list_endpoint(self):
		_, receipt_id = self._create_confirmed_receipt()
		res = self.client.post(
			"/api/payments/simulate/",
			{"receipt_id": receipt_id, "status": "COMPLETED"},
			format="json",
		)
		self.assertEqual(res.status_code, 201)
		payment_id = res.data["id"]

		res = self.client.get(f"/api/receipts/{receipt_id}/payments/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(len(res.data), 1)
		self.assertEqual(res.data[0]["id"], payment_id)
		self.assertEqual(res.data[0]["status"], "COMPLETED")

		res = self.client.get(f"/api/payments/{payment_id}/")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["id"], payment_id)
		self.assertEqual(res.data["receipt"], receipt_id)
