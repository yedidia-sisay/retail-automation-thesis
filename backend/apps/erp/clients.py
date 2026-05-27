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
	"""
	XML-RPC client for the Odoo 17 instance running in erp/docker-compose.yml.

	Architecture rule
	-----------------
	Only confirmed, cashier-approved transactions are pushed to Odoo.
	YOLO must never write directly to Odoo.

	Configuration (Django settings / .env)
	---------------------------------------
	ODOO_URL       — e.g. http://localhost:8069
	ODOO_DB        — e.g. odoo_retail
	ODOO_USERNAME  — e.g. admin
	ODOO_PASSWORD  — e.g. admin
	"""

	erp_system: str = "ODOO"

	def __init__(self, *, url: str, db: str, username: str, password: str):
		self.url = url.rstrip("/")
		self.db = db
		self.username = username
		self.password = password
		self._uid: int | None = None

	# ── Internal helpers ───────────────────────────────────────────────────

	def _common(self):
		import xmlrpc.client
		return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")

	def _models(self):
		import xmlrpc.client
		return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

	def _get_uid(self) -> int:
		if self._uid is None:
			uid = self._common().authenticate(self.db, self.username, self.password, {})
			if not uid:
				raise ERPClientError(
					f"Odoo authentication failed for user '{self.username}' on db '{self.db}'."
				)
			self._uid = uid
		return self._uid

	def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
		try:
			return self._models().execute_kw(
				self.db, self._get_uid(), self.password,
				model, method, list(args), kwargs,
			)
		except Exception as exc:
			raise ERPClientError(f"Odoo XML-RPC error ({model}.{method}): {exc}") from exc

	# ── Public API ─────────────────────────────────────────────────────────

	def sync_products(self) -> list[dict[str, Any]]:
		"""
		Pull all POS-available products from Odoo and return them in the
		standard format expected by apps.erp.services.sync_products_from_erp().

		Returns a list of dicts with keys:
		    erp_product_id, sku, name, barcode, unit_type, current_price
		"""
		product_ids = self._execute(
			"product.product", "search",
			[["available_in_pos", "=", True], ["active", "=", True]],
		)
		if not product_ids:
			return []

		records = self._execute(
			"product.product", "read",
			product_ids,
			fields=["id", "name", "default_code", "barcode", "list_price", "uom_id"],
		)

		results: list[dict[str, Any]] = []
		for r in records:
			uom_name = r["uom_id"][1] if r.get("uom_id") else ""
			unit_type = "KG" if "kg" in uom_name.lower() else "PIECE"
			results.append({
				"erp_product_id": str(r["id"]),
				"sku": r.get("default_code") or "",
				"name": r.get("name") or "",
				"barcode": r.get("barcode") or "",
				"unit_type": unit_type,
				"current_price": str(r.get("list_price", "0.00")),
			})
		return results

	def push_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
		"""
		Push a confirmed receipt to Odoo as a POS order.

		Architecture rule: only call this after the cashier has confirmed
		the transaction. YOLO detections must never trigger this directly.

		The payload format is produced by apps.erp.services.build_receipt_erp_payload().
		"""
		receipt_number = payload.get("receipt_number") or "UNKNOWN"

		# Build POS order lines: (0, 0, {vals}) create commands
		order_lines = []
		for line in payload.get("lines", []):
			erp_product_id = line.get("erp_product_id")
			if not erp_product_id:
				# Try to look up by SKU
				sku = line.get("sku") or ""
				if sku:
					ids = self._execute(
						"product.product", "search",
						[["default_code", "=", sku], ["active", "=", True]],
					)
					erp_product_id = str(ids[0]) if ids else None

			if not erp_product_id:
				continue  # skip unresolvable products

			try:
				qty = float(line.get("quantity", 1))
				price = float(line.get("unit_price", 0))
			except (TypeError, ValueError):
				qty, price = 1.0, 0.0

			order_lines.append((0, 0, {
				"product_id": int(erp_product_id),
				"qty": qty,
				"price_unit": price,
				"price_subtotal": qty * price,
				"price_subtotal_incl": qty * price,
			}))

		if not order_lines:
			return {
				"success": False,
				"erp_system": self.erp_system,
				"erp_reference": None,
				"error": "No resolvable order lines — receipt not pushed to Odoo.",
			}

		# Find the first open POS session
		session_ids = self._execute(
			"pos.session", "search",
			[["state", "=", "opened"]],
		)
		if not session_ids:
			return {
				"success": False,
				"erp_system": self.erp_system,
				"erp_reference": None,
				"error": "No open POS session found in Odoo. Open 'Cashier Terminal 1' first.",
			}
		session_id = session_ids[0]

		# Determine payment method (prefer Cash)
		cash_method_ids = self._execute(
			"pos.payment.method", "search",
			[["name", "=", "Cash"]],
		)
		payment_method_id = cash_method_ids[0] if cash_method_ids else None

		try:
			total = float(payload.get("total", 0))
		except (TypeError, ValueError):
			total = 0.0

		payments = []
		if payment_method_id:
			payments.append((0, 0, {
				"payment_method_id": payment_method_id,
				"amount": total,
			}))

		order_vals = {
			"session_id": session_id,
			"lines": order_lines,
			"payment_ids": payments,
			"amount_total": total,
			"amount_paid": total,
			"amount_return": 0.0,
			"amount_tax": 0.0,
			"pos_reference": f"Order {receipt_number}",
			"name": f"Order {receipt_number}",
		}

		order_id = self._execute("pos.order", "create", order_vals)
		erp_reference = f"ODOO-POS-{order_id}"

		return {
			"success": True,
			"erp_system": self.erp_system,
			"erp_reference": erp_reference,
			"erp_order_id": order_id,
			"message": f"Receipt {receipt_number} pushed to Odoo POS as order ID {order_id}.",
		}

	def get_receipt_status(self, erp_reference: str) -> dict[str, Any]:
		"""Check the status of a previously pushed POS order."""
		# erp_reference format: "ODOO-POS-{order_id}"
		try:
			order_id = int(erp_reference.split("-")[-1])
		except (ValueError, IndexError):
			return {"erp_reference": erp_reference, "status": "UNKNOWN"}

		orders = self._execute(
			"pos.order", "read",
			[order_id],
			fields=["id", "name", "state", "pos_reference"],
		)
		if not orders:
			return {"erp_reference": erp_reference, "status": "NOT_FOUND"}

		order = orders[0]
		state_map = {
			"draft": "PENDING",
			"paid": "SYNCED",
			"done": "SYNCED",
			"invoiced": "SYNCED",
			"cancel": "CANCELLED",
		}
		return {
			"erp_reference": erp_reference,
			"status": state_map.get(order.get("state", ""), "UNKNOWN"),
			"odoo_state": order.get("state"),
			"odoo_name": order.get("name"),
		}
