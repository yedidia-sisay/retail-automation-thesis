from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.audit.services import log_audit_event
from apps.checkout.models import CheckoutSession
from apps.receipts.models import Receipt

from .models import Payment


def _quantize_money(value: Decimal) -> Decimal:
	return (value or Decimal("0.00")).quantize(Decimal("0.01"))


def validate_receipt_can_be_paid(receipt: Receipt) -> None:
	if receipt.payment_status == Receipt.PaymentStatus.PAID:
		raise ValidationError({"detail": "This receipt is already paid."})

	if receipt.total is None:
		raise ValidationError({"detail": "Receipt total is missing."})

	if _quantize_money(receipt.total) <= Decimal("0.00"):
		raise ValidationError({"detail": "Receipt total must be greater than zero."})


def mark_receipt_paid(receipt: Receipt, payment: Payment) -> None:
	receipt.payment_status = Receipt.PaymentStatus.PAID
	receipt.save(update_fields=["payment_status", "updated_at"])


def mark_payment_failed(receipt: Receipt, payment: Payment) -> None:
	receipt.payment_status = Receipt.PaymentStatus.PAYMENT_FAILED
	receipt.save(update_fields=["payment_status", "updated_at"])


def _map_payment_status_to_receipt_status(payment_status: str) -> str:
	if payment_status == Payment.Status.COMPLETED:
		return Receipt.PaymentStatus.PAID
	if payment_status == Payment.Status.PENDING:
		return Receipt.PaymentStatus.PAYMENT_PENDING
	if payment_status == Payment.Status.CANCELLED:
		return Receipt.PaymentStatus.PAYMENT_CANCELLED
	if payment_status == Payment.Status.FAILED:
		return Receipt.PaymentStatus.PAYMENT_FAILED
	return Receipt.PaymentStatus.UNPAID


def _update_session_status_for_payment(*, session: CheckoutSession, payment_status: str) -> None:
	# Sprint 8: keep state machine minimal. Confirmation remains the source of truth
	# for locking edits. Payment status is recorded for reporting/demo.
	if payment_status == Payment.Status.PENDING:
		if hasattr(CheckoutSession.Status, "PAYMENT_PENDING"):
			session.status = CheckoutSession.Status.PAYMENT_PENDING
			session.save(update_fields=["status", "updated_at"])
		return

	if payment_status == Payment.Status.COMPLETED:
		if hasattr(CheckoutSession.Status, "COMPLETED"):
			session.status = CheckoutSession.Status.COMPLETED
			session.save(update_fields=["status", "updated_at"])
		return

	# FAILED/CANCELLED: keep session confirmed so cashier can retry payment.
	if session.status != CheckoutSession.Status.CONFIRMED:
		session.status = CheckoutSession.Status.CONFIRMED
		session.save(update_fields=["status", "updated_at"])


def _generate_transaction_reference(payment: Payment) -> str:
	date_part = timezone.localdate().strftime("%Y%m%d")
	sequence_part = str(payment.id).zfill(6)
	return f"SIM-{date_part}-{sequence_part}"


def simulate_payment(
	*,
	receipt_id: int,
	method: str = Payment.Method.DEMO,
	status: str = Payment.Status.COMPLETED,
	amount: Decimal | None = None,
	user=None,
	provider_response: dict | None = None,
) -> Payment:
	with transaction.atomic():
		try:
			receipt = (
				Receipt.objects.select_for_update()
				.select_related("checkout_session")
				.get(pk=receipt_id)
			)
		except Receipt.DoesNotExist as exc:
			raise NotFound("Receipt not found.") from exc

		validate_receipt_can_be_paid(receipt)

		receipt_total = _quantize_money(receipt.total)
		payment_amount = _quantize_money(amount) if amount is not None else receipt_total

		if payment_amount != receipt_total:
			raise ValidationError({"detail": "Payment amount must match receipt total."})

		payment = Payment.objects.create(
			receipt=receipt,
			checkout_session=receipt.checkout_session,
			amount=payment_amount,
			method=method,
			status=status,
			provider_name="SIMULATED",
			provider_response=provider_response or {},
			created_by=user if getattr(user, "is_authenticated", False) else None,
		)

		if not payment.transaction_reference:
			payment.transaction_reference = _generate_transaction_reference(payment)
			payment.save(update_fields=["transaction_reference", "updated_at"])

		receipt.payment_status = _map_payment_status_to_receipt_status(payment.status)
		receipt.save(update_fields=["payment_status", "updated_at"])

		_update_session_status_for_payment(session=receipt.checkout_session, payment_status=payment.status)

		# Optional audit events (Sprint 8)
		event_type = "PAYMENT_SIMULATED"
		if payment.status == Payment.Status.COMPLETED:
			event_type = "PAYMENT_COMPLETED"
		elif payment.status == Payment.Status.FAILED:
			event_type = "PAYMENT_FAILED"
		elif payment.status == Payment.Status.CANCELLED:
			event_type = "PAYMENT_CANCELLED"
		elif payment.status == Payment.Status.PENDING:
			event_type = "PAYMENT_PENDING"

		log_audit_event(
			user=user if getattr(user, "is_authenticated", False) else None,
			checkout_session=receipt.checkout_session,
			event_type=event_type,
			description=f"Simulated payment {payment.status} via {payment.method}.",
			metadata={
				"receipt_id": receipt.id,
				"payment_id": payment.id,
				"amount": str(payment.amount),
				"method": payment.method,
				"status": payment.status,
				"transaction_reference": payment.transaction_reference,
			},
		)

		return payment


def get_payment(*, payment_id: int) -> Payment:
	try:
		return Payment.objects.select_related("receipt", "checkout_session").get(pk=payment_id)
	except Payment.DoesNotExist as exc:
		raise NotFound("Payment not found.") from exc


def list_payments_for_receipt(*, receipt_id: int):
	return Payment.objects.filter(receipt_id=receipt_id).order_by("-created_at")
