from __future__ import annotations

from django.shortcuts import get_object_or_404

from apps.receipts.models import Receipt


def get_receipt_detail(receipt_id: int) -> Receipt:
	return get_object_or_404(
		Receipt.objects.select_related("cashier", "checkout_session").prefetch_related("lines"),
		pk=receipt_id,
	)
