from __future__ import annotations

from decimal import Decimal
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from PIL import Image

from apps.catalog.models import Category, DetectionClassMapping, Product
from apps.checkout.models import CheckoutItem, CheckoutSession
from apps.vision.models import DetectedObject, DetectionRun


def _make_test_png_bytes() -> bytes:
	buf = io.BytesIO()
	img = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
	img.save(buf, format="PNG")
	return buf.getvalue()


class VisionDetectionIntegrationTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.category = Category.objects.create(name="Drinks", slug="drinks")
		self.product = Product.objects.create(
			category=self.category,
			name="Coca Cola 500ml",
			sku="COCA500",
			unit_type=Product.UnitType.PIECE,
			current_price=Decimal("35.00"),
			is_active=True,
		)
		self.session = CheckoutSession.objects.create(status=CheckoutSession.Status.OPEN)

	def _upload_image(self):
		image = SimpleUploadedFile(
			"frame.png",
			_make_test_png_bytes(),
			content_type="image/png",
		)
		return self.client.post(
			"/api/vision/detect/",
			data={"checkout_session_id": self.session.id, "image": image},
			format="multipart",
		)

	def test_detect_creates_run_objects_and_grouped_checkout_item(self):
		DetectionClassMapping.objects.create(
			class_name="coca_cola_500ml",
			product=self.product,
			minimum_confidence=Decimal("0.80"),
			is_active=True,
		)

		resp = self._upload_image()
		self.assertEqual(resp.status_code, 200)

		run = DetectionRun.objects.first()
		self.assertIsNotNone(run)
		self.assertEqual(run.status, DetectionRun.Status.COMPLETED)

		self.assertEqual(DetectedObject.objects.filter(detection_run=run).count(), 2)

		item = CheckoutItem.objects.get(checkout_session=self.session, source=CheckoutItem.Source.VISION)
		self.assertEqual(item.product_id, self.product.id)
		self.assertEqual(item.status, CheckoutItem.Status.ACTIVE)
		self.assertEqual(item.quantity, Decimal("2.000"))
		self.assertEqual(item.subtotal, Decimal("70.00"))

		session = CheckoutSession.objects.get(pk=self.session.pk)
		self.assertEqual(session.total_amount, Decimal("70.00"))

	def test_needs_review_blocks_confirmation(self):
		DetectionClassMapping.objects.create(
			class_name="coca_cola_500ml",
			product=self.product,
			minimum_confidence=Decimal("0.95"),
			is_active=True,
		)

		resp = self._upload_image()
		self.assertEqual(resp.status_code, 200)

		item = CheckoutItem.objects.get(checkout_session=self.session, source=CheckoutItem.Source.VISION)
		self.assertEqual(item.status, CheckoutItem.Status.NEEDS_REVIEW)

		confirm = self.client.post(f"/api/checkout/sessions/{self.session.id}/confirm/")
		self.assertEqual(confirm.status_code, 400)
		self.assertIn("need review", str(confirm.data).lower())
