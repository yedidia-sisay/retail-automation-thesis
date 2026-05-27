# ─────────────────────────────────────────────────────────────────────────────
# Retail Checkout Automation — Makefile
#
# Infrastructure (Docker):  Odoo 17 + PostgreSQL
# Local processes:          Django · YOLO service · Cashier UI
#
# Usage:
#   make setup        # first-time setup (run once)
#   make dev          # start the full dev stack
#   make odoo         # start/stop Odoo infrastructure only
#   make down         # stop Odoo Docker containers
#   make reset        # wipe Odoo data (requires re-setup)
#   make logs         # tail all local logs
#   make logs s=yolo  # tail a specific service log
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: setup dev odoo down reset logs migrate seed help

.DEFAULT_GOAL := help

## setup: First-time setup — installs deps, starts Odoo, seeds all data
setup:
	@bash scripts/setup.sh

## dev: Start the full dev stack (Odoo in Docker + Django/YOLO/UI locally)
dev:
	@bash scripts/dev.sh

## odoo: Start Odoo infrastructure in the background (Docker only)
odoo:
	docker compose -f erp/docker-compose.yml up -d
	@echo "Odoo running at http://localhost:8069"

## down: Stop Odoo Docker containers (data preserved)
down:
	docker compose -f erp/docker-compose.yml down

## reset: Stop Odoo and delete all its data (requires re-setup)
reset:
	@bash scripts/reset.sh

## reset-full: Reset Odoo AND wipe Django db + media (requires re-setup)
reset-full:
	@bash scripts/reset.sh --full

## logs: Tail logs — use `make logs s=<service>` for a specific one
logs:
	@bash scripts/logs.sh $(s)

## migrate: Run Django migrations
migrate:
	backend/.venv/bin/python backend/manage.py migrate --noinput

## seed: Re-seed Django catalogue and users
seed:
	backend/.venv/bin/python backend/manage.py seed_catalog
	backend/.venv/bin/python backend/manage.py seed_users

## help: Show this help
help:
	@echo ""
	@echo "Retail Checkout Automation — available targets:"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /' | column -t -s ':'
	@echo ""
