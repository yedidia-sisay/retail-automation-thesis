#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# dev.sh — Start the full development stack
#
# Infrastructure (Docker):
#   odoo-db  — PostgreSQL 15
#   odoo     — Odoo 17 (http://localhost:8069)
#
# Local processes (your venvs / node):
#   backend     — Django dev server  (http://localhost:8000)
#   yolo        — FastAPI/uvicorn    (http://localhost:8061)
#   cashier-ui  — Vite dev server    (http://localhost:3000)
#
# All three local processes run in the background and their logs are written
# to logs/<service>.log. A single Ctrl+C stops everything cleanly.
#
# Usage:
#   ./scripts/dev.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[dev]${NC} $*"; }
success() { echo -e "${GREEN}[dev]${NC} $*"; }
warn()    { echo -e "${YELLOW}[dev]${NC} $*"; }
error()   { echo -e "${RED}[dev]${NC} $*" >&2; }

# ── Preflight ─────────────────────────────────────────────────────────────────
if [ ! -f "backend/.venv/bin/python" ]; then
    error "backend/.venv not found. Run ./scripts/setup.sh first."
    exit 1
fi
if [ ! -f ".venv/bin/uvicorn" ]; then
    error ".venv/bin/uvicorn not found. Run ./scripts/setup.sh first."
    exit 1
fi
if [ ! -d "cashier-ui/node_modules" ]; then
    error "cashier-ui/node_modules not found. Run ./scripts/setup.sh first."
    exit 1
fi

# docker compose v2 vs v1
if docker compose version &>/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Always use the canonical Odoo compose file
COMPOSE_CMD="$DOCKER_COMPOSE -f erp/docker-compose.yml"

# ── Log directory ─────────────────────────────────────────────────────────────
mkdir -p logs

# ── PID tracking ─────────────────────────────────────────────────────────────
PIDS=()

cleanup() {
    echo ""
    info "Shutting down local services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    success "All local services stopped."
    echo ""
    info "Odoo is still running in Docker."
    info "Stop it with: $COMPOSE_CMD down"
    echo ""
}
trap cleanup INT TERM EXIT

# ── 1. Ensure Odoo infrastructure is up ──────────────────────────────────────
info "Ensuring Odoo infrastructure is running..."
$COMPOSE_CMD up -d

# Quick readiness check (don't wait as long as setup.sh — it should already be up)
ODOO_WAIT=60
ELAPSED=0
until curl -sf http://localhost:8069/web/health &>/dev/null; do
    if [ $ELAPSED -ge $ODOO_WAIT ]; then
        warn "Odoo health check timed out — it may still be starting."
        warn "Check with: $COMPOSE_CMD logs odoo"
        break
    fi
    printf "."
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
[ $ELAPSED -gt 0 ] && echo ""
success "Odoo ready at http://localhost:8069"

# ── 2. Start Django backend ───────────────────────────────────────────────────
info "Starting Django backend → logs/backend.log"
backend/.venv/bin/python backend/manage.py runserver 0.0.0.0:8000 \
    > logs/backend.log 2>&1 &
PIDS+=($!)
success "Django started (PID ${PIDS[-1]})"

# ── 3. Start YOLO service ─────────────────────────────────────────────────────
info "Starting YOLO service → logs/yolo.log"
(
    cd yolo_service
    ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload
) > logs/yolo.log 2>&1 &
PIDS+=($!)
success "YOLO service started (PID ${PIDS[-1]})"

# ── 4. Start Cashier UI ───────────────────────────────────────────────────────
info "Starting Cashier UI → logs/cashier-ui.log"
npm --prefix cashier-ui run dev \
    > logs/cashier-ui.log 2>&1 &
PIDS+=($!)
success "Cashier UI started (PID ${PIDS[-1]})"

# ── 5. Print service map ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Dev stack is running${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Service         URL                       Log"
echo "  ─────────────── ───────────────────────── ──────────────────────"
echo "  Cashier UI      http://localhost:3000      logs/cashier-ui.log"
echo "  Django backend  http://localhost:8000      logs/backend.log"
echo "  YOLO service    http://localhost:8061      logs/yolo.log"
echo "  Odoo ERP        http://localhost:8069      docker compose logs odoo"
echo ""
echo "  Press Ctrl+C to stop all local services."
echo ""

# ── 6. Tail all logs to the terminal ─────────────────────────────────────────
# Give processes a moment to write their first lines
sleep 2
tail -f logs/backend.log logs/yolo.log logs/cashier-ui.log &
PIDS+=($!)

# Wait until Ctrl+C
wait
