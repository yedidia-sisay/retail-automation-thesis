from __future__ import annotations

from decimal import Decimal

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.receipts.selectors import get_receipt_detail
from apps.receipts.serializers import ReceiptSerializer


def _format_money(value: Decimal) -> str:
	return f"{value.quantize(Decimal('0.01'))}"


def _build_printable_text(receipt) -> str:
	lines = []
	lines.append("STORE NAME")
	lines.append("------------------------------")
	lines.append(f"Receipt: {receipt.receipt_number}")
	lines.append(f"Date: {receipt.created_at:%Y-%m-%d %H:%M:%S}")
	cashier = getattr(receipt.cashier, "username", None) or "-"
	lines.append(f"Cashier: {cashier}")
	lines.append("------------------------------")

	for line in receipt.lines.all():
		qty = str(line.quantity)
		unit_price = _format_money(line.unit_price)
		subtotal = _format_money(line.subtotal)
		lines.append(f"{line.product_name}")
		lines.append(f"  {qty} x {unit_price} = {subtotal}")

	lines.append("------------------------------")
	lines.append(f"TOTAL: {_format_money(receipt.total)}")
	lines.append(f"Payment: {receipt.payment_status}")
	return "\n".join(lines) + "\n"


class ReceiptDetailAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, receipt_id: int):
		receipt = get_receipt_detail(receipt_id=receipt_id)
		serializer = ReceiptSerializer(receipt)
		return Response(serializer.data)


class ReceiptPrintPreviewAPIView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, receipt_id: int):
		receipt = get_receipt_detail(receipt_id=receipt_id)
		serializer = ReceiptSerializer(receipt)
		data = dict(serializer.data)
		data["printable_text"] = _build_printable_text(receipt)
		return Response(data)
