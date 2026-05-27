#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# logs.sh — Tail logs for local services or Odoo
#
# Usage:
#   ./scripts/logs.sh                  # tail all local service logs
#   ./scripts/logs.sh backend          # Django backend
#   ./scripts/logs.sh yolo             # YOLO service
#   ./scripts/logs.sh cashier-ui       # Cashier UI
#   ./scripts/logs.sh odoo             # Odoo (via docker compose)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SERVICE="${1:-}"

case "$SERVICE" in
    odoo)
        docker compose -f erp/docker-compose.yml logs -f odoo
        ;;
    backend)
        tail -f logs/backend.log
        ;;
    yolo)
        tail -f logs/yolo.log
        ;;
    cashier-ui|ui)
        tail -f logs/cashier-ui.log
        ;;
    "")
        # All local logs
        if ls logs/*.log &>/dev/null 2>&1; then
            tail -f logs/backend.log logs/yolo.log logs/cashier-ui.log
        else
            echo "No log files found. Start the stack first with ./scripts/dev.sh"
            exit 1
        fi
        ;;
    *)
        echo "Unknown service: $SERVICE"
        echo "Valid options: backend, yolo, cashier-ui, odoo"
        exit 1
        ;;
esac
