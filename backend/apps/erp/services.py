from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Category, Product, ProductBarcode
from apps.erp.clients import (
	BaseERPClient,
	ERPClientConfigurationError,
	FakeOdooClient,
	RealOdooClient,
)
from apps.erp.models import ERPProductMapping, ERPReceiptMapping, ERPSyncLog
from apps.receipts.models import Receipt


def get_erp_client() -> BaseERPClient:
	mode = (getattr(settings, "ERP_CLIENT_MODE", "FAKE") or "FAKE").upper().strip()
	if mode == "FAKE":
		return FakeOdooClient()

	if mode == "ODOO":
		url = (getattr(settings, "ODOO_URL", "") or "").strip()
		db = (getattr(settings, "ODOO_DB", "") or "").strip()
		username = (getattr(settings, "ODOO_USERNAME", "") or "").strip()
		password = (getattr(settings, "ODOO_PASSWORD", "") or "").strip()
		missing = [k for k, v in {"ODOO_URL": url, "ODOO_DB": db, "ODOO_USERNAME": username, "ODOO_PASSWORD": password}.items() if not v]
		if missing:
			raise ERPClientConfigurationError(
				"ERP_CLIENT_MODE=ODOO selected but missing credentials: " + ", ".join(missing)
			)
		return RealOdooClient(url=url, db=db, username=username, password=password)

	raise ERPClientConfigurationError(f"Unknown ERP_CLIENT_MODE '{mode}'.")


def _money_str(value: Decimal) -> str:
	return f"{value.quantize(Decimal('0.01'))}"


def _qty_str(value: Decimal) -> str:
	return f"{value.quantize(Decimal('0.001'))}"


def build_receipt_erp_payload(receipt: Receipt) -> dict[str, Any]:
	# Load related objects (safe even if caller already prefetched).
	receipt = (
		Receipt.objects.select_related("checkout_session", "cashier")
		.prefetch_related("lines", "lines__product", "lines__product__barcodes")
		.get(pk=receipt.pk)
	)

	product_ids = [line.product_id for line in receipt.lines.all() if line.product_id]
	mappings = {
		m.product_id: m
		for m in ERPProductMapping.objects.filter(product_id__in=product_ids, is_active=True)
	}

	lines_out: list[dict[str, Any]] = []
	for line in receipt.lines.all():
		product = line.product
		erp_product_id = None
		barcode = None
		unit_type = None
		sku = line.product_sku

		if product is not None:
			mapping = mappings.get(product.id)
			if mapping is not None:
				erp_product_id = mapping.erp_product_id
			elif getattr(product, "odoo_product_id", None):
				erp_product_id = product.odoo_product_id

			unit_type = getattr(product, "unit_type", None)
			primary = None
			try:
				primary = next((b for b in product.barcodes.all() if b.is_primary), None)
			except Exception:
				primary = None
			if primary is None:
				first = next(iter(product.barcodes.all()), None)
				barcode = getattr(first, "barcode", None)
			else:
				barcode = primary.barcode

		lines_out.append(
			{
				"product_id": product.id if product is not None else None,
				"erp_product_id": erp_product_id,
				"product_name": line.product_name,
				"sku": sku,
				"barcode": barcode,
				"quantity": _qty_str(Decimal(line.quantity)),
				"unit_type": unit_type,
				"unit_price": _money_str(Decimal(line.unit_price)),
				"subtotal": _money_str(Decimal(line.subtotal)),
			}
		)

	cashier_username = getattr(receipt.cashier, "username", None) if receipt.cashier_id else None

	return {
		"receipt_number": receipt.receipt_number,
		"receipt_id": receipt.id,
		"checkout_session_id": receipt.checkout_session_id,
		"cashier": cashier_username,
		"created_at": receipt.created_at.isoformat(),
		"payment_status": receipt.payment_status,
		"total": _money_str(Decimal(receipt.total)),
		"lines": lines_out,
	}


@dataclass(frozen=True)
class ERPReceiptPushResult:
	receipt_id: int
	erp_status: str
	erp_reference: str | None
	message: str
	error: str | None = None


def _validate_receipt_can_sync(receipt: Receipt) -> None:
	session = receipt.checkout_session
	if session.status in {"OPEN", "CANCELLED"}:
		raise ValidationError("Receipt ERP sync is only allowed after checkout confirmation.")


def push_receipt_to_erp(
	*,
	receipt_id: int,
	user=None,
	action: str = ERPSyncLog.Action.PUSH_RECEIPT,
) -> ERPReceiptPushResult:
	try:
		receipt = (
			Receipt.objects.select_related("checkout_session", "cashier")
			.prefetch_related("lines", "lines__product", "lines__product__barcodes")
			.get(pk=receipt_id)
		)
	except Receipt.DoesNotExist:
		raise ValidationError({"receipt_id": "Receipt not found."})

	_validate_receipt_can_sync(receipt)

	payload = build_receipt_erp_payload(receipt)

	log = ERPSyncLog.objects.create(
		object_type=ERPSyncLog.ObjectType.RECEIPT,
		object_id=str(receipt.id),
		action=action,
		status=ERPSyncLog.Status.PENDING,
		erp_system="ODOO",
		request_payload=payload,
	)

	# Mark receipt as pending immediately; if anything fails we still have a trace.
	receipt.erp_status = Receipt.ERPStatus.PENDING
	receipt.save(update_fields=["erp_status", "updated_at"])

	try:
		client = get_erp_client()
		response = client.push_receipt(payload)
		success = bool(response.get("success"))
		erp_reference = response.get("erp_reference")
		message = response.get("message") or "ERP push completed."
		if success:
			now = timezone.now()
			with transaction.atomic():
				receipt.refresh_from_db()
				receipt.erp_status = Receipt.ERPStatus.SYNCED
				receipt.erp_reference = erp_reference
				receipt.erp_synced_at = now
				receipt.save(
					update_fields=["erp_status", "erp_reference", "erp_synced_at", "updated_at"]
				)

				ERPReceiptMapping.objects.update_or_create(
					receipt=receipt,
					erp_system="ODOO",
					defaults={
						"erp_reference": erp_reference,
						"sync_status": ERPReceiptMapping.SyncStatus.SYNCED,
						"request_payload": payload,
						"response_payload": response,
						"error_message": "",
						"synced_at": now,
					},
				)

				log.status = ERPSyncLog.Status.SUCCESS
				log.response_payload = response
				log.error_message = ""
				log.save(update_fields=["status", "response_payload", "error_message"])

			return ERPReceiptPushResult(
				receipt_id=receipt.id,
				erp_status=receipt.erp_status,
				erp_reference=erp_reference,
				message=message,
			)

		error_message = response.get("error") or response.get("message") or "ERP sync failed."
		with transaction.atomic():
			receipt.refresh_from_db()
			receipt.erp_status = Receipt.ERPStatus.FAILED
			receipt.save(update_fields=["erp_status", "updated_at"])

			ERPReceiptMapping.objects.update_or_create(
				receipt=receipt,
				erp_system="ODOO",
				defaults={
					"erp_reference": erp_reference,
					"sync_status": ERPReceiptMapping.SyncStatus.FAILED,
					"request_payload": payload,
					"response_payload": response,
					"error_message": error_message,
					"synced_at": None,
				},
			)

			log.status = ERPSyncLog.Status.FAILED
			log.response_payload = response
			log.error_message = error_message
			log.save(update_fields=["status", "response_payload", "error_message"])

		return ERPReceiptPushResult(
			receipt_id=receipt.id,
			erp_status=Receipt.ERPStatus.FAILED,
			erp_reference=erp_reference,
			message="ERP sync failed, but checkout remains completed.",
			error=error_message,
		)

	except Exception as exc:
		error_message = str(exc)
		with transaction.atomic():
			receipt.refresh_from_db()
			receipt.erp_status = Receipt.ERPStatus.FAILED
			receipt.save(update_fields=["erp_status", "updated_at"])

			ERPReceiptMapping.objects.update_or_create(
				receipt=receipt,
				erp_system="ODOO",
				defaults={
					"sync_status": ERPReceiptMapping.SyncStatus.FAILED,
					"request_payload": payload,
					"response_payload": {},
					"error_message": error_message,
					"synced_at": None,
				},
			)

			log.status = ERPSyncLog.Status.FAILED
			log.response_payload = {}
			log.error_message = error_message
			log.save(update_fields=["status", "response_payload", "error_message"])

		return ERPReceiptPushResult(
			receipt_id=receipt.id,
			erp_status=Receipt.ERPStatus.FAILED,
			erp_reference=None,
			message="ERP sync failed, but checkout remains completed.",
			error=error_message,
		)


def retry_receipt_erp_sync(*, receipt_id: int, user=None) -> ERPReceiptPushResult:
	receipt = Receipt.objects.filter(pk=receipt_id).select_related("checkout_session").first()
	if receipt is None:
		raise ValidationError({"receipt_id": "Receipt not found."})

	allowed = {
		Receipt.ERPStatus.NOT_SYNCED,
		Receipt.ERPStatus.PENDING,
		Receipt.ERPStatus.FAILED,
		Receipt.ERPStatus.RETRY_REQUIRED,
	}
	if receipt.erp_status not in allowed:
		raise ValidationError(
			{"detail": f"Cannot retry ERP sync when receipt.erp_status is '{receipt.erp_status}'."}
		)

	return push_receipt_to_erp(receipt_id=receipt_id, user=user, action=ERPSyncLog.Action.RETRY_SYNC)


def sync_products_from_erp(*, create_missing: bool = False, user=None) -> dict[str, Any]:
	log = ERPSyncLog.objects.create(
		object_type=ERPSyncLog.ObjectType.PRODUCT,
		object_id="*",
		action=ERPSyncLog.Action.SYNC_PRODUCTS,
		status=ERPSyncLog.Status.PENDING,
		erp_system="ODOO",
		request_payload={"create_missing": bool(create_missing)},
	)

	created_count = 0
	updated_count = 0
	skipped_count = 0
	failed_count = 0

	try:
		client = get_erp_client()
		products = client.sync_products() or []

		default_category = None
		if create_missing:
			default_category, _ = Category.objects.get_or_create(
				slug="erp-imported",
				defaults={"name": "ERP Imported", "description": "Imported from ERP sync"},
			)

		for p in products:
			try:
				sku = (p.get("sku") or "").strip()
				barcode = (p.get("barcode") or "").strip()
				erp_product_id = (p.get("erp_product_id") or "").strip()
				name = (p.get("name") or "").strip()
				unit_type = (p.get("unit_type") or Product.UnitType.PIECE).strip()
				price_raw = p.get("current_price")
				price = Decimal(str(price_raw)) if price_raw is not None else Decimal("0.00")

				if not erp_product_id:
					failed_count += 1
					continue

				product = None
				if sku:
					product = Product.objects.filter(sku=sku).first()
				if product is None and barcode:
					barcode_obj = ProductBarcode.objects.select_related("product").filter(
						barcode=barcode
					).first()
					product = barcode_obj.product if barcode_obj else None

				if product is None:
					if not create_missing:
						skipped_count += 1
						continue

					if default_category is None:
						# Defensive; should be set when create_missing True.
						default_category = Category.objects.create(
							name="ERP Imported",
							slug="erp-imported",
						)

					product = Product.objects.create(
						category=default_category,
						name=name or sku or erp_product_id,
						sku=sku or f"ERP-{erp_product_id}",
						unit_type=unit_type if unit_type in Product.UnitType.values else Product.UnitType.PIECE,
						current_price=price,
						is_active=True,
					)
					created_count += 1

					if barcode:
						ProductBarcode.objects.get_or_create(
							product=product,
							barcode=barcode,
							defaults={"is_primary": True},
						)

				mapping, created = ERPProductMapping.objects.update_or_create(
					product=product,
					erp_system="ODOO",
					defaults={
						"erp_product_id": erp_product_id,
						"erp_product_name": name,
						"last_synced_at": timezone.now(),
						"is_active": True,
					},
				)

				# Maintain backward-compatible single-field mapping too.
				if getattr(product, "odoo_product_id", None) != erp_product_id:
					product.odoo_product_id = erp_product_id
					product.last_synced_at = timezone.now()
					product.sync_status = Product.SyncStatus.SYNCED
					product.save(update_fields=["odoo_product_id", "last_synced_at", "sync_status", "updated_at"])

				if not created:
					updated_count += 1

			except Exception:
				failed_count += 1

		summary = {
			"created_count": created_count,
			"updated_count": updated_count,
			"skipped_count": skipped_count,
			"failed_count": failed_count,
			"total_erp_products": len(products),
		}

		log.status = ERPSyncLog.Status.SUCCESS
		log.response_payload = {"summary": summary}
		log.error_message = ""
		log.save(update_fields=["status", "response_payload", "error_message"])
		return summary

	except Exception as exc:
		error_message = str(exc)
		log.status = ERPSyncLog.Status.FAILED
		log.response_payload = {}
		log.error_message = error_message
		log.save(update_fields=["status", "response_payload", "error_message"])
		return {
			"created_count": created_count,
			"updated_count": updated_count,
			"skipped_count": skipped_count,
			"failed_count": failed_count + 1,
			"error": error_message,
		}
