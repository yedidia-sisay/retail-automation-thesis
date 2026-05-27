#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — First-time project setup
#
# Run this once before starting the dev stack for the first time.
# Safe to re-run — all steps are idempotent.
#
# What it does:
#   1. Checks prerequisites (docker, python3, node, npm)
#   2. Copies .env files from examples if they don't exist
#   3. Creates Python venvs and installs dependencies for backend + yolo_service
#   4. Installs frontend npm dependencies
#   5. Starts Odoo in Docker and waits for it to be ready
#   6. Runs the Odoo setup script (creates DB, installs modules, seeds products)
#   7. Exports Odoo product IDs for Django sync
#   8. Runs Django migrations and seeds the local catalogue
#
# Usage:
#   ./scripts/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[setup]${NC} $*"; }
success() { echo -e "${GREEN}[setup]${NC} $*"; }
warn()    { echo -e "${YELLOW}[setup]${NC} $*"; }
error()   { echo -e "${RED}[setup]${NC} $*" >&2; }
header()  { echo -e "\n${BOLD}$*${NC}"; }

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
header "── Checking prerequisites ──────────────────────────────────────────────"

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        error "Required command not found: $1"
        error "Please install $1 and re-run this script."
        exit 1
    fi
    success "$1 found"
}

check_cmd docker
check_cmd node
check_cmd npm
check_cmd python3

# docker compose v2 (plugin) vs v1 (standalone)
if docker compose version &>/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    error "docker compose not found. Install Docker Desktop or the compose plugin."
    exit 1
fi
success "docker compose found ($DOCKER_COMPOSE)"

# Always use the canonical Odoo compose file
COMPOSE_CMD="$DOCKER_COMPOSE -f erp/docker-compose.yml"

# ── 2. .env files ─────────────────────────────────────────────────────────────
header "── Environment files ───────────────────────────────────────────────────"

copy_env() {
    local dest="$1"
    local src="$2"
    if [ ! -f "$dest" ]; then
        if [ -f "$src" ]; then
            cp "$src" "$dest"
            success "Created $dest"
        else
            warn "$src not found — skipping $dest"
        fi
    else
        info "$dest already exists, skipping."
    fi
}

copy_env ".env"                  ".env.example"
copy_env "backend/.env"          "backend/.env.example"
copy_env "yolo_service/.env"     "yolo_service/.env.example"
copy_env "cashier-ui/.env"       "cashier-ui/.env.example"

# ── 3. Backend Python venv ────────────────────────────────────────────────────
header "── Backend — Python venv ───────────────────────────────────────────────"

if [ ! -d "backend/.venv" ]; then
    info "Creating backend/.venv..."
    python3 -m venv backend/.venv
    success "Created backend/.venv"
else
    info "backend/.venv already exists."
fi

info "Installing backend dependencies..."
backend/.venv/bin/pip3 install --quiet --upgrade pip
backend/.venv/bin/pip3 install --quiet -r backend/requirements.txt
success "Backend dependencies installed."

# ── 4. YOLO service Python venv ───────────────────────────────────────────────
header "── YOLO service — Python venv ──────────────────────────────────────────"

info "Installing YOLO service dependencies into root .venv (this may take a while — ultralytics is large)..."
.venv/bin/pip3 install --quiet --upgrade pip
.venv/bin/pip3 install --quiet -r yolo_service/requirements.txt
success "YOLO service dependencies installed."

# ── 5. YOLO weights check ─────────────────────────────────────────────────────
header "── YOLO weights ────────────────────────────────────────────────────────"

WEIGHTS_PATH="yolo_service/models/best.pt"
mkdir -p yolo_service/models
if [ ! -f "$WEIGHTS_PATH" ]; then
    warn "Weights not found at $WEIGHTS_PATH"
    warn "The YOLO service will start in degraded mode."
    warn "Set USE_MOCK_YOLO=True in backend/.env to use mock detections."
else
    success "Weights found at $WEIGHTS_PATH"
fi

# ── 6. Frontend npm dependencies ──────────────────────────────────────────────
header "── Cashier UI — npm dependencies ──────────────────────────────────────"

info "Running npm install in cashier-ui/..."
npm --prefix cashier-ui install --silent
success "Frontend dependencies installed."

# ── 7. Start Odoo infrastructure ──────────────────────────────────────────────
header "── Odoo — starting Docker containers ──────────────────────────────────"

info "Starting odoo-db and odoo containers..."
$COMPOSE_CMD up -d

info "Waiting for Odoo to be ready (first run downloads ~1.5 GB and can take 3–5 min)..."
ODOO_TIMEOUT=360
ELAPSED=0
until curl -sf http://localhost:8069/web/health &>/dev/null; do
    if [ $ELAPSED -ge $ODOO_TIMEOUT ]; then
        error "Odoo did not become ready within ${ODOO_TIMEOUT}s."
        error "Check logs with: $COMPOSE_CMD logs odoo"
        exit 1
    fi
    printf "."
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo ""
success "Odoo is ready at http://localhost:8069"

# ── 8. Odoo setup ─────────────────────────────────────────────────────────────
header "── Odoo — initial configuration ───────────────────────────────────────"

info "Running Odoo setup (creates DB, installs modules, seeds 21 products)..."
python3 erp/scripts/setup_odoo.py
success "Odoo setup complete."

info "Exporting Odoo product IDs → erp/data/odoo_product_ids.json..."
python3 erp/scripts/export_odoo_ids.py
success "Product IDs exported."

# ── 9. Django migrations + seed ───────────────────────────────────────────────
header "── Django — migrations and seed data ──────────────────────────────────"

info "Running migrations..."
backend/.venv/bin/python backend/manage.py migrate --noinput
success "Migrations applied."

info "Seeding product catalogue..."
backend/.venv/bin/python backend/manage.py seed_catalog
success "Catalogue seeded."

info "Seeding users (admin + cashier)..."
backend/.venv/bin/python backend/manage.py seed_users
success "Users seeded."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete! Run the dev stack with:${NC}"
echo ""
echo -e "    ${CYAN}./scripts/dev.sh${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
