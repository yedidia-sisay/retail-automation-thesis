from __future__ import annotations

from typing import Any

from apps.audit.models import AuditEvent


def log_audit_event(
	*,
	user=None,
	checkout_session=None,
	event_type: str,
	description: str = "",
	metadata: dict[str, Any] | None = None,
) -> None:
	# Audit logging must never break checkout flows.
	try:
		AuditEvent.objects.create(
			user=user,
			checkout_session=checkout_session,
			event_type=(event_type or "").strip() or "UNKNOWN",
			description=description or "",
			metadata=metadata or {},
		)
	except Exception:
		return
