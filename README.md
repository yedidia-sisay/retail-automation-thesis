# AI Retail Checkout Automation System

A thesis project that automates supermarket checkout using YOLO object detection, a Django REST backend, a React cashier interface, and Odoo as the ERP/POS system.

The core principle: **AI detection results are suggestions, not the final bill.** The cashier always remains in control. Only cashier-confirmed transactions are recorded.

---

## Table of contents

1. [System overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Project structure](#3-project-structure)
4. [Services and ports](#4-services-and-ports)
5. [Prerequisites](#5-prerequisites)
6. [Quick start — full system](#6-quick-start--full-system)
7. [Django backend](#7-django-backend)
8. [YOLO inference service](#8-yolo-inference-service)
9. [Cashier UI](#9-cashier-ui)
10. [Odoo ERP](#10-odoo-erp)
11. [Product catalogue](#11-product-catalogue)
12. [Credentials](#12-credentials)
13. [Checkout workflow](#13-checkout-workflow)
14. [Django–Odoo integration](#14-djangoodoo-integration)
15. [Environment variables reference](#15-environment-variables-reference)
16. [Running tests](#16-running-tests)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. System overview

This system replaces the manual barcode-scanning step at a supermarket checkout with AI-assisted product detection. A camera captures items on the checkout table, a YOLO model identifies them, and the cashier reviews and confirms the suggested receipt before payment.

A second camera handles weighted products (fruits, vegetables) — the system identifies the item and reads the scale weight to calculate the price.

Odoo 17 acts as the official ERP and POS system. Django coordinates the checkout flow. The YOLO service performs detection only and has no access to Odoo.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Cashier UI (React)                          │
│                      http://localhost:3000                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────────┐
│                    Django Backend (DRF)                             │
│                      http://localhost:8000                          │
│                                                                     │
│  accounts · catalog · vision · checkout · barcode                   │
│  weighted_items · receipts · payments · erp · audit                 │
└──────┬──────────────────────────────────────────┬───────────────────┘
       │ HTTP (image upload)                      │ XML-RPC
       │                                          │ (confirmed orders only)
┌──────▼──────────────┐               ┌───────────▼───────────────────┐
│  YOLO Service       │               │  Odoo 17 ERP/POS              │
│  (FastAPI)          │               │  http://localhost:8069         │
│  http://localhost   │               │                               │
│  :8061              │               │  PostgreSQL 15                 │
│                     │               │  http://localhost:5432         │
│  Returns:           │               └───────────────────────────────┘
│  class_id           │
│  class_name         │
│  confidence         │
│  bbox               │
└─────────────────────┘
```

**Data flow for a checkout transaction:**

```
Camera frame
  → YOLO Service          (detects objects, returns class names + confidence)
  → Django Backend        (maps classes to products, creates draft checkout items)
  → Cashier UI            (cashier reviews, corrects, confirms)
  → Django Backend        (generates receipt, processes payment)
  → Odoo ERP              (records confirmed POS order via XML-RPC)
```

**Architecture rules:**
- YOLO must never write to Odoo directly.
- Only cashier-confirmed transactions are pushed to Odoo.
- Django keeps a local product catalogue so checkout works even if Odoo is offline.
- Detection results are draft suggestions until the cashier accepts them.

---

## 3. Project structure

```
thesis/
├── backend/                    Django REST API
│   ├── apps/
│   │   ├── accounts/           Authentication, users, roles
│   │   ├── catalog/            Products, categories, barcodes, YOLO mappings
│   │   ├── vision/             YOLO client, detection runs, detected objects
│   │   ├── checkout/           Checkout sessions, items, corrections
│   │   ├── barcode/            Barcode fallback scanning
│   │   ├── weighted_items/     Weighted product detection and pricing
│   │   ├── receipts/           Receipt generation and storage
│   │   ├── payments/           Payment simulation
│   │   ├── erp/                Odoo XML-RPC integration
│   │   └── audit/              Audit logging and evaluation data
│   ├── config/                 Django settings, URLs, WSGI
│   ├── manage.py
│   ├── pyproject.toml
│   └── .env
│
├── cashier-ui/                 React + TypeScript + Vite frontend
│   ├── src/
│   ├── package.json
│   └── .env
│
├── yolo_service/               FastAPI YOLO inference microservice
│   ├── app/
│   │   ├── main.py             FastAPI app and routes
│   │   ├── detector.py         YOLO model wrapper
│   │   ├── schemas.py          Pydantic request/response models
│   │   └── config.py           Settings from .env
│   ├── models/
│   │   └── best.pt             Trained YOLO weights (not committed)
│   ├── requirements.txt
│   └── .env
│
├── erp/                        Odoo ERP Docker deployment
│   ├── docker-compose.yml      Odoo 17 + PostgreSQL 15
│   ├── config/odoo.conf        Odoo server configuration
│   ├── scripts/
│   │   ├── setup_odoo.py       One-time automated configuration
│   │   ├── export_odoo_ids.py  Export product IDs for Django sync
│   │   └── health_check.py     Connectivity check
│   ├── data/
│   │   ├── products_reference.json   Static product catalogue
│   │   └── odoo_product_ids.json     Generated after setup
│   └── .env
│
├── design/                     Design documents
│   ├── cashier_ui.md           Full UI specification
│   ├── django_plan.md          Backend architecture plan
│   └── checkout_dashboard_reference.html
│
└── thesis/                     Thesis document (Typst)
    └── main.typ
```

---

## 4. Services and ports

| Service | URL | Notes |
|---------|-----|-------|
| Django backend | http://localhost:8000 | REST API |
| Cashier UI | http://localhost:3000 | React dev server |
| YOLO service | http://localhost:8061 | FastAPI inference |
| Odoo ERP | http://localhost:8069 | Web UI + XML-RPC |
| PostgreSQL | localhost:5432 | Odoo database (Docker) |
| Django admin | http://localhost:8000/admin | |
| Odoo POS | http://localhost:8069/odoo/point-of-sale | |
| YOLO API docs | http://localhost:8061/docs | Swagger UI |

---

## 5. Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Docker and Docker Compose
- YOLO model weights at `yolo_service/models/best.pt`

**Install Docker (if not installed):**
```bash
# Ubuntu/Debian
sudo apt install docker.io docker-compose-plugin

# Add yourself to the docker group (avoids needing sudo)
sudo usermod -aG docker $USER
newgrp docker   # apply without logging out
```

---

## 6. Quick start — full system

### Step 1 — Start Odoo ERP

```bash
docker compose -f erp/docker-compose.yml up -d
```

Wait ~60 seconds for first-time initialisation, then:

```bash
# Create the database and configure everything
python3 erp/scripts/setup_odoo.py

# Export Odoo product IDs for Django
python3 erp/scripts/export_odoo_ids.py
```

Odoo is now at http://localhost:8069 — login: `admin` / `admin`

### Step 2 — Start the Django backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"   # or: pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Seed the product catalogue
python manage.py seed_catalog

# Seed demo users (admin + cashier)
python manage.py seed_users

# Start the server
python manage.py runserver
```

Django is now at http://localhost:8000

### Step 3 — Start the YOLO service

```bash
cd yolo_service

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Place your trained weights at models/best.pt
uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload
```

YOLO service is now at http://localhost:8061

### Step 4 — Start the Cashier UI

```bash
cd cashier-ui
npm install
npm run dev
```

Cashier UI is now at http://localhost:3000

---

## 7. Django backend

### Apps

| App | Responsibility |
|-----|---------------|
| `accounts` | Session-based auth, users, roles (Admin / Cashier) |
| `catalog` | Products, categories, barcodes, YOLO class mappings, prices |
| `vision` | YOLO HTTP client, detection runs, detected objects |
| `checkout` | Checkout sessions, draft items, cashier corrections |
| `barcode` | Barcode fallback — scan to add product |
| `weighted_items` | Weighted product detection, scale reading, price calculation |
| `receipts` | Receipt generation, line items, print preview |
| `payments` | Payment simulation (Cash, Telebirr, Chapa) |
| `erp` | Odoo XML-RPC client, product sync, receipt push, sync logs |
| `audit` | Correction events, fallback counts, evaluation data |

### Key API endpoints

```
# Auth
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/me/

# Products
GET    /api/products/
GET    /api/products/search/?q=cola
GET    /api/products/barcode/{barcode}/

# Checkout
POST   /api/checkout/sessions/
GET    /api/checkout/sessions/{id}/
POST   /api/checkout/sessions/{id}/add-detections/
POST   /api/checkout/sessions/{id}/add-barcode/
POST   /api/checkout/sessions/{id}/add-manual-item/
POST   /api/checkout/sessions/{id}/add-weighted-item/
PATCH  /api/checkout/items/{id}/
DELETE /api/checkout/items/{id}/
POST   /api/checkout/sessions/{id}/confirm/
POST   /api/checkout/sessions/{id}/cancel/

# Vision
POST   /api/vision/detect/

# Receipts
GET    /api/receipts/{id}/
GET    /api/receipts/{id}/print-preview/

# Payments
POST   /api/payments/simulate/

# ERP
POST   /api/erp/sync-products/
POST   /api/erp/push-receipt/{receipt_id}/
GET    /api/erp/sync-logs/
```

### Management commands

```bash
# Seed the product catalogue (17 YOLO products + categories + barcodes)
python manage.py seed_catalog

# Seed demo users
python manage.py seed_users

# Run migrations
python manage.py migrate
```

### Checkout item sources

Every item on a receipt is tagged with its source:

| Source | Meaning |
|--------|---------|
| `VISION` | Detected by YOLO, accepted by cashier |
| `BARCODE` | Added via barcode scanner fallback |
| `MANUAL` | Added manually by cashier |
| `WEIGHTED` | Weighted product with scale reading |

### Confidence thresholds

| Confidence | Behaviour |
|-----------|-----------|
| ≥ 0.80 | Auto-suggested as normal draft item |
| 0.50 – 0.79 | Draft item marked `NEEDS_REVIEW` |
| < 0.50 | Not added; shown as unknown suggestion |

### ERP client modes

Set `ERP_CLIENT_MODE` in `backend/.env`:

| Mode | Behaviour |
|------|-----------|
| `FAKE` | Uses `FakeOdooClient` — deterministic responses, no Odoo needed. Default for tests. |
| `ODOO` | Uses `RealOdooClient` — connects to the Odoo container via XML-RPC. |

---

## 8. YOLO inference service

A lightweight FastAPI microservice that runs YOLO object detection and returns raw detections only. It has no knowledge of prices, checkout sessions, or Odoo.

**Returns per detection:**
```json
{
  "class_id": 0,
  "class_name": "Coca Cola",
  "confidence": 0.91,
  "bbox": { "x1": 120, "y1": 80, "x2": 300, "y2": 410 }
}
```

**Configuration (`yolo_service/.env`):**

```env
MODEL_PATH=models/best.pt
CONFIDENCE_THRESHOLD=0.50
DEVICE=cpu
```

**Mock mode** — if `USE_MOCK_YOLO=True` in `backend/.env`, Django skips the HTTP call and returns fixture data (2× Coca Cola detections). Useful for development without a GPU.

**API docs:** http://localhost:8061/docs

---

## 9. Cashier UI

React 19 + TypeScript + Vite + Tailwind CSS frontend.

### Core pages

| Route | Purpose |
|-------|---------|
| `/login` | Cashier / admin login |
| `/cashier` | Home — start new checkout, view recent transactions |
| `/cashier/session/:id` | Main checkout dashboard (3-column layout) |
| `/receipts/:id` | Receipt detail |
| `/receipts/:id/print` | Print preview |
| `/transactions` | Transaction history |
| `/settings` | Camera selection, API URLs |
| `/help` | Troubleshooting guide |
| `/shift` | Shift summary |
| `/returns` | Returns / refunds |

### Main checkout dashboard layout

```
┌──────────────────┬──────────────────────────┬──────────────────┐
│  LEFT            │  MIDDLE                  │  RIGHT           │
│                  │                          │                  │
│  Packaged        │  Packaged Detection      │  Receipt         │
│  Camera Feed     │  Review                  │  Preview         │
│                  │                          │                  │
│  Weighted        │  Weighted Item           │  Totals          │
│  Scale Feed      │  Review                  │                  │
│                  │                          │  Payment         │
│  Barcode /       │  Confirmed               │  Panel           │
│  Manual          │  Checkout Items          │                  │
└──────────────────┴──────────────────────────┴──────────────────┘
```

### Running

```bash
cd cashier-ui
npm install
npm run dev       # development server on port 3000
npm run build     # production build
```

### Environment

```env
# cashier-ui/.env
# Leave empty — Vite proxies /api/* to http://localhost:8000
VITE_API_BASE_URL=
```

---

## 10. Odoo ERP

Odoo 17 Community Edition running in Docker. Acts as the official ERP and POS system for the demo.

### Start / stop

```bash
# Start (from project root)
docker compose -f erp/docker-compose.yml up -d

# Stop (data preserved)
docker compose -f erp/docker-compose.yml down

# Full reset — deletes all data
docker compose -f erp/docker-compose.yml down -v

# View logs
docker compose -f erp/docker-compose.yml logs -f odoo
```

### First-time setup

Run once after the containers are healthy:

```bash
# Configure company, modules, products, POS, users, payment methods
python3 erp/scripts/setup_odoo.py

# Export Odoo product IDs to JSON for Django
python3 erp/scripts/export_odoo_ids.py

# Verify everything
python3 erp/scripts/health_check.py
```

### Installed modules

| Module | Purpose |
|--------|---------|
| `point_of_sale` | POS terminal, sessions, orders |
| `stock` | Inventory |
| `account` | Invoicing and accounting |
| `sale_management` | Sales orders |

### Accessing Odoo

| What | URL |
|------|-----|
| Web UI | http://localhost:8069 |
| POS interface | http://localhost:8069/odoo/point-of-sale |
| Database manager | http://localhost:8069/web/database/manager |

### Opening the POS session

1. Log in at http://localhost:8069 as `admin` / `admin`
2. Go to **Point of Sale → Dashboard**
3. Click **Open** on **Cashier Terminal 1**

---

## 11. Product catalogue

21 products configured in both Django and Odoo. 17 match the YOLO model's trained classes. 4 are weighted products sold by kilogram.

| SKU | Name | Category | UoM | Price (ETB) | Barcode | YOLO class |
|-----|------|----------|-----|-------------|---------|------------|
| COCA-COLA | Coca Cola | Beverages | Unit | 35.00 | 100000000001 | Coca Cola |
| PEPSI | Pepsi | Beverages | Unit | 33.00 | 100000000002 | Pepsi |
| SOL-WATER | Sol Water | Beverages | Unit | 25.00 | 100000000010 | Sol Water |
| CAPPUCCINO | Cappuccino | Beverages | Unit | 45.00 | 100000000011 | Cappuccino |
| DOVE-SOAP | Dove Soap | Packaged Products | Unit | 85.00 | 100000000003 | Dove Soap |
| DURU-SOAP | Duru Soap | Packaged Products | Unit | 75.00 | 100000000004 | Duru Soap |
| MAWELL-PASTA | Mawell Pasta | Packaged Products | Unit | 95.00 | 100000000005 | Mawell Pasta |
| OMAAR-TUNA | Omaar Tuna | Packaged Products | Unit | 120.00 | 100000000006 | Omaar Tuna |
| ABOUNDED-BISCUIT | Abounded Biscuit | Packaged Products | Unit | 55.00 | 100000000007 | Abounded Biscuit |
| NICE-SMALL-SOFT | Nice Small Soft | Packaged Products | Unit | 40.00 | 100000000008 | Nice Small Soft |
| BRAVO-TISSUE | Bravo Tissue Paper | Packaged Products | Unit | 65.00 | 100000000009 | Bravo Tissue Paper |
| EVE-COMFORT | Eve Comfort | Packaged Products | Unit | 110.00 | 100000000012 | Eve Comfort |
| DETERGENT | Detergent | Packaged Products | Unit | 130.00 | 100000000013 | detergent |
| BLUE-SUNCHIPS | Blue Sunchips | Packaged Products | Unit | 50.00 | 100000000014 | Blue Sunchips |
| YELLOW-SUNCHIPS | Yellow Sunchips | Packaged Products | Unit | 50.00 | 100000000015 | Yellow Sunchips |
| RED-QQ-SNACK | Red QQ Snack | Packaged Products | Unit | 30.00 | 100000000016 | Red QQ snack |
| DECOY | Decoy | Packaged Products | Unit | 20.00 | 100000000017 | Decoy |
| BANANA-KG | Banana (per kg) | Weighted Products | kg | 45.00 | 200000000001 | — |
| APPLE-KG | Apple (per kg) | Weighted Products | kg | 80.00 | 200000000002 | — |
| TOMATO-KG | Tomato (per kg) | Weighted Products | kg | 35.00 | 200000000003 | — |
| ONION-KG | Onion (per kg) | Weighted Products | kg | 30.00 | 200000000004 | — |

All prices are in Ethiopian Birr (ETB).

---

## 12. Credentials

### Django

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| Admin | `admin` | (set via `createsuperuser`) | Full Django admin access |
| Cashier | `adamreta` | (set by `seed_users`) | POS checkout access |

### Odoo

| Role | Login | Password |
|------|-------|----------|
| Admin | `admin` | `admin` |
| Cashier | `cashier` | `cashier123` |
| DB master password | — | `retail_master_2024` |

### PostgreSQL (Odoo database)

| Field | Value |
|-------|-------|
| Host | `localhost:5432` |
| Database | `odoo_retail` |
| User | `odoo` |
| Password | `odoo_secret_2024` |

---

## 13. Checkout workflow

The complete flow from camera to confirmed receipt:

```
1. Cashier starts a new checkout session
   POST /api/checkout/sessions/

2. Cashier captures or uploads an image of packaged products
   POST /api/vision/detect/
   → Django sends image to YOLO service
   → YOLO returns detections (class_name, confidence, bbox)
   → Django maps class names to products via DetectionClassMapping
   → Draft checkout items are created

3. Cashier reviews detection results in the UI
   - High confidence (≥ 0.80): shown as normal suggestion
   - Low confidence (0.50–0.79): shown with "Needs Review" badge
   - Unknown class: shown as unresolved, cashier must scan or search

4. Cashier corrects the draft
   - Accept correct detections
   - Replace wrong products
   - Adjust quantities
   - Remove incorrect items

5. Cashier adds any missed items
   - Barcode scan: POST /api/checkout/sessions/{id}/add-barcode/
   - Manual search: POST /api/checkout/sessions/{id}/add-manual-item/

6. For weighted products (fruits/vegetables)
   - Cashier places item on scale, captures weighted camera feed
   - System identifies product and reads weight
   - POST /api/checkout/sessions/{id}/add-weighted-item/
   - Price = weight × unit price per kg

7. Cashier confirms the checkout
   POST /api/checkout/sessions/{id}/confirm/
   → Receipt is generated
   → Receipt is locked (no further edits)

8. Payment
   POST /api/payments/simulate/
   → Payment method: Cash / Telebirr (Simulated) / Chapa (Simulated)
   → Receipt payment_status updated to PAID

9. ERP sync (if ERP_CLIENT_MODE=ODOO)
   POST /api/erp/push-receipt/{receipt_id}/
   → RealOdooClient creates a pos.order in Odoo via XML-RPC
   → Odoo order ID stored in Receipt.erp_reference
```

---

## 14. Django–Odoo integration

### Syncing products from Odoo → Django

Django's `sync_products_from_erp()` fetches all POS-available products from Odoo and updates `Product.odoo_product_id` and `ERPProductMapping`.

```bash
# Via API
POST /api/erp/sync-products/

# Via Django shell
python manage.py shell -c "
from apps.erp.services import sync_products_from_erp
print(sync_products_from_erp(create_missing=False))
"

# Via exported JSON (offline)
python3 erp/scripts/export_odoo_ids.py
# then import the JSON into Django manually
```

### Pushing confirmed receipts to Odoo

After a cashier confirms a transaction, Django calls `push_receipt_to_erp()` which:

1. Builds a receipt payload with all line items and product IDs
2. Finds the open POS session in Odoo
3. Creates a `pos.order` via XML-RPC
4. Stores the Odoo order ID in `Receipt.erp_reference`

**To enable real Odoo integration**, set in `backend/.env`:

```env
ERP_CLIENT_MODE=ODOO
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_retail
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

Leave `ERP_CLIENT_MODE=FAKE` for development and testing — the fake client returns deterministic responses without needing Odoo running.

### ERP sync statuses

| Status | Meaning |
|--------|---------|
| `NOT_SYNCED` | Receipt not yet pushed to Odoo |
| `PENDING` | Push in progress |
| `SYNCED` | Successfully recorded in Odoo |
| `FAILED` | Push failed — checkout still complete |
| `RETRY_REQUIRED` | Queued for retry |

---

## 15. Environment variables reference

### `backend/.env`

```env
SECRET_KEY=django-insecure-change-this-later
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# YOLO service
USE_MOCK_YOLO=False              # True = skip HTTP call, return fixture data
YOLO_SERVICE_URL=http://127.0.0.1:8061
YOLO_SERVICE_TIMEOUT=30

# Odoo ERP
ERP_CLIENT_MODE=FAKE             # FAKE or ODOO
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_retail
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### `yolo_service/.env`

```env
MODEL_PATH=models/best.pt
CONFIDENCE_THRESHOLD=0.50
DEVICE=cpu                       # cpu or cuda
HOST=0.0.0.0
PORT=8061
```

### `erp/.env`

```env
POSTGRES_DB=odoo_retail
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo_secret_2024
ODOO_PORT=8069
ODOO_MASTER_PASSWORD=retail_master_2024
```

---

## 16. Running tests

### Django backend

```bash
cd backend
source .venv/bin/activate

# Run all tests
python manage.py test

# Run with coverage
coverage run manage.py test
coverage report

# Property-based tests (Hypothesis)
python manage.py test apps.accounts.tests
```

### YOLO service

```bash
cd yolo_service
source .venv/bin/activate
pytest
```

### Cashier UI

```bash
cd cashier-ui
npm run lint
npm run build   # type-check + build
```

---

## 17. Troubleshooting

### Docker / Odoo

**Permission denied connecting to Docker socket**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Odoo shows 500 / "Database not found"**
```bash
# The database needs to be initialised
python3 erp/scripts/setup_odoo.py
```

**Odoo module installation hangs**
```bash
# First-time install takes 3–5 minutes — check logs
docker compose -f erp/docker-compose.yml logs -f odoo
```

**Port 8069 already in use**
```bash
# Change ODOO_PORT in erp/.env, then restart
docker compose -f erp/docker-compose.yml down
docker compose -f erp/docker-compose.yml up -d
```

**POS session won't open**
→ Go to Point of Sale → Configuration → Point of Sale → edit "Cashier Terminal 1" and confirm at least one payment method is assigned.

### Django

**Migrations fail**
```bash
python manage.py migrate --run-syncdb
```

**YOLO service unreachable**
```bash
# Check the service is running
curl http://localhost:8061/health

# Or enable mock mode in backend/.env
USE_MOCK_YOLO=True
```

**ERP sync fails but checkout still works**
→ This is by design. Set `ERP_CLIENT_MODE=FAKE` to disable Odoo sync during development.

### YOLO service

**`models/best.pt` not found**
→ Place your trained YOLO weights at `yolo_service/models/best.pt`. The file is not committed to git.

**CUDA out of memory**
→ Set `DEVICE=cpu` in `yolo_service/.env`.

---

## Design documents

| Document | Location |
|----------|----------|
| Cashier UI specification | `design/cashier_ui.md` |
| Django backend architecture plan | `design/django_plan.md` |
| Checkout dashboard reference | `design/checkout_dashboard_reference.html` |
| Odoo ERP setup guide | `erp/README.md` |
| YOLO service guide | `yolo_service/README.md` |
| Thesis document | `thesis/main.typ` |
