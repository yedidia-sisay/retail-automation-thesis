from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ERPClientError(Exception):
	pass


class ERPClientConfigurationError(ERPClientError):
	pass


class BaseERPClient:
	"""ERP client abstraction.

	The rest of the backend must depend on this interface, not on Odoo specifics.
	"""

	erp_system: str = "ERP"

	def sync_products(self) -> list[dict[str, Any]]:
		raise NotImplementedError

	def push_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
		raise NotImplementedError

	def get_receipt_status(self, erp_reference: str) -> dict[str, Any]:
		raise NotImplementedError


@dataclass(frozen=True)
class FakeOdooClient(BaseERPClient):
	"""Simulated Odoo client for demos/tests.

	This client is the default to ensure tests never require a real Odoo server.
	"""

	erp_system: str = "ODOO-DEMO"

	def sync_products(self) -> list[dict[str, Any]]:
		# Keep this stable/deterministic for tests and demos.
		return [
			{
				"erp_product_id": "ODOO-PROD-001",
				"sku": "COCA-500",
				"name": "Coca Cola 500ml",
				"barcode": "5449000000996",
				"unit_type": "PIECE",
				"current_price": "35.00",
			},
			{
				"erp_product_id": "ODOO-PROD-002",
				"sku": "ERP-UNKNOWN-1",
				"name": "ERP Imported Product",
				"barcode": "9999999999999",
				"unit_type": "PIECE",
				"current_price": "10.00",
			},
		]

	def push_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
		receipt_number = payload.get("receipt_number") or "UNKNOWN"
		reference = f"ODOO-DEMO-{receipt_number}"
		return {
			"success": True,
			"erp_system": self.erp_system,
			"erp_reference": reference,
			"message": "Receipt pushed to simulated Odoo ERP successfully.",
		}

	def get_receipt_status(self, erp_reference: str) -> dict[str, Any]:
		return {
			"erp_reference": erp_reference,
			"status": "SYNCED",
		}


class RealOdooClient(BaseERPClient):
	"""Optional real Odoo client placeholder.

	Not used by default. Implement only if/when a live Odoo demo is required.
	"""

	erp_system: str = "ODOO"

	def __init__(self, *, url: str, db: str, username: str, password: str):
		self.url = url
		self.db = db
		self.username = username
		self.password = password

	def sync_products(self) -> list[dict[str, Any]]:
		raise NotImplementedError("RealOdooClient is optional and not implemented.")

	def push_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
		raise NotImplementedError("RealOdooClient is optional and not implemented.")

	def get_receipt_status(self, erp_reference: str) -> dict[str, Any]:
		raise NotImplementedError("RealOdooClient is optional and not implemented.")
