#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# reset.sh — Tear down Odoo Docker containers and wipe all persistent data
#
# WARNING: Deletes the Odoo PostgreSQL volume and Odoo filestore.
#          Django's local db.sqlite3 and media/ are NOT touched.
#          Re-run ./scripts/setup.sh afterwards to restore everything.
#
# Usage:
#   ./scripts/reset.sh
#   ./scripts/reset.sh --full    # also wipe Django db.sqlite3 and media/
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

FULL=false
for arg in "$@"; do
    [ "$arg" = "--full" ] && FULL=true
done

echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}  WARNING: This will delete the Odoo database and all Odoo data.${NC}"
if [ "$FULL" = true ]; then
echo -e "${RED}  --full: Django db.sqlite3 and media/ will also be deleted.${NC}"
fi
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
read -r -p "Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${YELLOW}[reset]${NC} Stopping Docker containers and removing volumes..."
docker compose -f erp/docker-compose.yml down -v --remove-orphans

if [ "$FULL" = true ]; then
    echo -e "${YELLOW}[reset]${NC} Removing Django db.sqlite3..."
    rm -f backend/db.sqlite3
    echo -e "${YELLOW}[reset]${NC} Removing Django media/..."
    rm -rf backend/media/*
fi

echo ""
echo -e "${GREEN}Reset complete.${NC}"
echo "Run ./scripts/setup.sh to set up the project again."
