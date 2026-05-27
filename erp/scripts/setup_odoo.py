#!/usr/bin/env python3
"""
setup_odoo.py — Automated Odoo configuration for the Retail Checkout Automation demo.

This script connects to a running Odoo instance via XML-RPC and:
  1. Installs required modules (point_of_sale, stock, account)
  2. Creates the demo company profile
  3. Creates product categories
  4. Creates units of measure (Unit, kg)
  5. Creates all 17 demo products with barcodes and prices
  6. Creates POS configuration ("Cashier Terminal 1")
  7. Creates payment methods (Cash, Telebirr, Chapa)
  8. Creates cashier user
  9. Prints a summary with all Odoo product IDs

Usage:
    python setup_odoo.py [--url URL] [--db DB] [--password MASTER_PASSWORD]

Defaults:
    --url      http://localhost:8069
    --db       odoo_retail
    --password retail_master_2024

Run AFTER Odoo is healthy:
    docker compose up -d
    # wait ~60 seconds for first-time init
    python scripts/setup_odoo.py
"""

from __future__ import annotations

import argparse
import sys
import time
import xmlrpc.client
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_URL = "http://localhost:8069"
DEFAULT_DB = "odoo_retail"
DEFAULT_MASTER_PASSWORD = "retail_master_2024"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"  # Odoo default; changed below after setup


# ─────────────────────────────────────────────────────────────────────────────
# Product catalogue — mirrors backend/apps/catalog/management/commands/seed_catalog.py
# ─────────────────────────────────────────────────────────────────────────────
PRODUCTS = [
    # ── Beverages ─────────────────────────────────────────────────────────
    {
        "name": "Coca Cola",
        "sku": "COCA-COLA",
        "barcode": "100000000001",
        "category": "Beverages",
        "unit_type": "PIECE",
        "price": 35.00,
    },
    {
        "name": "Pepsi",
        "sku": "PEPSI",
        "barcode": "100000000002",
        "category": "Beverages",
        "unit_type": "PIECE",
        "price": 33.00,
    },
    {
        "name": "Sol Water",
        "sku": "SOL-WATER",
        "barcode": "100000000010",
        "category": "Beverages",
        "unit_type": "PIECE",
        "price": 25.00,
    },
    {
        "name": "Cappuccino",
        "sku": "CAPPUCCINO",
        "barcode": "100000000011",
        "category": "Beverages",
        "unit_type": "PIECE",
        "price": 45.00,
    },
    # ── Packaged Products ─────────────────────────────────────────────────
    {
        "name": "Dove Soap",
        "sku": "DOVE-SOAP",
        "barcode": "100000000003",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 85.00,
    },
    {
        "name": "Duru Soap",
        "sku": "DURU-SOAP",
        "barcode": "100000000004",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 75.00,
    },
    {
        "name": "Mawell Pasta",
        "sku": "MAWELL-PASTA",
        "barcode": "100000000005",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 95.00,
    },
    {
        "name": "Omaar Tuna",
        "sku": "OMAAR-TUNA",
        "barcode": "100000000006",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 120.00,
    },
    {
        "name": "Abounded Biscuit",
        "sku": "ABOUNDED-BISCUIT",
        "barcode": "100000000007",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 55.00,
    },
    {
        "name": "Nice Small Soft",
        "sku": "NICE-SMALL-SOFT",
        "barcode": "100000000008",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 40.00,
    },
    {
        "name": "Bravo Tissue Paper",
        "sku": "BRAVO-TISSUE",
        "barcode": "100000000009",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 65.00,
    },
    {
        "name": "Eve Comfort",
        "sku": "EVE-COMFORT",
        "barcode": "100000000012",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 110.00,
    },
    {
        "name": "Detergent",
        "sku": "DETERGENT",
        "barcode": "100000000013",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 130.00,
    },
    {
        "name": "Blue Sunchips",
        "sku": "BLUE-SUNCHIPS",
        "barcode": "100000000014",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 50.00,
    },
    {
        "name": "Yellow Sunchips",
        "sku": "YELLOW-SUNCHIPS",
        "barcode": "100000000015",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 50.00,
    },
    {
        "name": "Red QQ Snack",
        "sku": "RED-QQ-SNACK",
        "barcode": "100000000016",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 30.00,
    },
    {
        "name": "Decoy",
        "sku": "DECOY",
        "barcode": "100000000017",
        "category": "Packaged Products",
        "unit_type": "PIECE",
        "price": 20.00,
    },
    # ── Weighted Products (sold by kg) ────────────────────────────────────
    {
        "name": "Banana (per kg)",
        "sku": "BANANA-KG",
        "barcode": "200000000001",
        "category": "Weighted Products",
        "unit_type": "KG",
        "price": 45.00,
    },
    {
        "name": "Apple (per kg)",
        "sku": "APPLE-KG",
        "barcode": "200000000002",
        "category": "Weighted Products",
        "unit_type": "KG",
        "price": 80.00,
    },
    {
        "name": "Tomato (per kg)",
        "sku": "TOMATO-KG",
        "barcode": "200000000003",
        "category": "Weighted Products",
        "unit_type": "KG",
        "price": 35.00,
    },
    {
        "name": "Onion (per kg)",
        "sku": "ONION-KG",
        "barcode": "200000000004",
        "category": "Weighted Products",
        "unit_type": "KG",
        "price": 30.00,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wait_for_odoo(url: str, timeout: int = 120) -> None:
    """Poll Odoo's /web/database/list until it responds."""
    print(f"Waiting for Odoo at {url} …", end="", flush=True)
    deadline = time.time() + timeout
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    while time.time() < deadline:
        try:
            common.version()
            print(" ready.")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(3)
    print()
    sys.exit(f"ERROR: Odoo did not become ready within {timeout}s. Is the container running?")


def _ensure_db(url: str, db: str, master_password: str) -> None:
    """Create the database if it doesn't exist yet."""
    db_proxy = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    existing = db_proxy.list()
    if db in existing:
        print(f"Database '{db}' already exists — skipping creation.")
        return
    print(f"Creating database '{db}' …")
    db_proxy.create_database(master_password, db, False, "en_US", ADMIN_PASSWORD)
    print("Database created.")
    # Give Odoo a moment to finish initialising
    time.sleep(10)


def _login(url: str, db: str, username: str, password: str) -> tuple[Any, Any, int]:
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        sys.exit(f"ERROR: Cannot authenticate as '{username}'. Check credentials.")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return common, models, uid


def _execute(models: Any, db: str, uid: int, password: str,
             model: str, method: str, *args, **kwargs) -> Any:
    # Odoo XML-RPC execute_kw signature:
    #   execute_kw(db, uid, password, model, method, args_list, kwargs_dict)
    # args_list  = positional arguments (list)
    # kwargs_dict = keyword arguments (dict) — e.g. {"fields": [...], "limit": 10}
    return models.execute_kw(db, uid, password, model, method, list(args), kwargs)


def _read(models: Any, db: str, uid: int, password: str,
          model: str, ids: list, fields: list) -> list:
    """Convenience wrapper for model.read() with field selection."""
    return models.execute_kw(
        db, uid, password, model, "read", [ids], {"fields": fields}
    )


def _search_read(models: Any, db: str, uid: int, password: str,
                 model: str, domain: list, fields: list, limit: int = 0) -> list:
    """Convenience wrapper for model.search_read()."""
    kwargs: dict = {"fields": fields}
    if limit:
        kwargs["limit"] = limit
    return models.execute_kw(db, uid, password, model, "search_read", [domain], kwargs)


def _find_or_create(models, db, uid, password, model, domain, values) -> int:
    ids = _execute(models, db, uid, password, model, "search", domain)
    if ids:
        return ids[0]
    return _execute(models, db, uid, password, model, "create", values)


# ─────────────────────────────────────────────────────────────────────────────
# Setup steps
# ─────────────────────────────────────────────────────────────────────────────

def install_modules(models, db, uid, password) -> None:
    print("\n[1/9] Installing modules …")
    required = ["point_of_sale", "stock", "account", "sale_management"]
    for module_name in required:
        ids = _execute(models, db, uid, password, "ir.module.module", "search",
                       [["name", "=", module_name]])
        if not ids:
            print(f"  WARNING: module '{module_name}' not found in registry — skipping.")
            continue
        module = _read(models, db, uid, password, "ir.module.module",
                       ids, ["name", "state"])[0]
        if module["state"] == "installed":
            print(f"  {module_name}: already installed")
        else:
            print(f"  {module_name}: installing …")
            _execute(models, db, uid, password, "ir.module.module", "button_immediate_install",
                     ids)
            print(f"  {module_name}: done")


def configure_company(models, db, uid, password) -> int:
    print("\n[2/9] Configuring company …")
    company_ids = _execute(models, db, uid, password, "res.company", "search",
                           [["id", "=", 1]])
    company_id = company_ids[0]
    _execute(models, db, uid, password, "res.company", "write", [company_id], {
        "name": "Retail Demo Supermarket",
        "street": "Bole Road, Addis Ababa",
        "city": "Addis Ababa",
        "country_id": _find_or_create(
            models, db, uid, password,
            "res.country",
            [["code", "=", "ET"]],
            {"name": "Ethiopia", "code": "ET"},
        ),
        "currency_id": _find_or_create(
            models, db, uid, password,
            "res.currency",
            [["name", "=", "ETB"]],
            {"name": "ETB", "symbol": "Br", "full_name": "Ethiopian Birr"},
        ),
        "phone": "+251911000000",
        "email": "pos@retaildemo.et",
        "website": "https://retaildemo.et",
    })
    print(f"  Company ID {company_id}: 'Retail Demo Supermarket' configured.")
    return company_id


def create_product_categories(models, db, uid, password) -> dict[str, int]:
    print("\n[3/9] Creating product categories …")
    categories = {
        "All": None,
        "Beverages": "All",
        "Packaged Products": "All",
        "Weighted Products": "All",
    }
    cat_ids: dict[str, int] = {}

    # Get root "All" category
    all_ids = _execute(models, db, uid, password, "pos.category", "search",
                       [["name", "=", "All"]])
    if all_ids:
        cat_ids["All"] = all_ids[0]
    else:
        cat_ids["All"] = _execute(models, db, uid, password, "pos.category", "create",
                                  {"name": "All"})

    for cat_name, parent_name in categories.items():
        if cat_name == "All":
            continue
        parent_id = cat_ids.get(parent_name) if parent_name else False
        existing = _execute(models, db, uid, password, "pos.category", "search",
                            [["name", "=", cat_name]])
        if existing:
            cat_ids[cat_name] = existing[0]
            print(f"  '{cat_name}': exists (ID {existing[0]})")
        else:
            vals = {"name": cat_name}
            if parent_id:
                vals["parent_id"] = parent_id
            cat_ids[cat_name] = _execute(models, db, uid, password, "pos.category", "create", vals)
            print(f"  '{cat_name}': created (ID {cat_ids[cat_name]})")

    # Also create internal product.category entries
    internal_cats: dict[str, int] = {}
    for cat_name in ["Beverages", "Packaged Products", "Weighted Products"]:
        existing = _execute(models, db, uid, password, "product.category", "search",
                            [["name", "=", cat_name]])
        if existing:
            internal_cats[cat_name] = existing[0]
        else:
            internal_cats[cat_name] = _execute(
                models, db, uid, password, "product.category", "create",
                {"name": cat_name}
            )

    return cat_ids, internal_cats


def get_uom_ids(models, db, uid, password) -> dict[str, int]:
    print("\n[4/9] Resolving units of measure …")
    uom_ids: dict[str, int] = {}

    # Unit (piece)
    unit_ids = _execute(models, db, uid, password, "uom.uom", "search",
                        [["name", "in", ["Unit(s)", "Units", "Unit", "pcs", "Piece(s)"]]])
    if unit_ids:
        uom_ids["PIECE"] = unit_ids[0]
        name = _read(models, db, uid, password, "uom.uom",
                     [unit_ids[0]], ["name"])[0]["name"]
        print(f"  PIECE → '{name}' (ID {unit_ids[0]})")
    else:
        # Create a Unit UoM
        uom_cat_ids = _execute(models, db, uid, password, "uom.category", "search",
                               [["name", "=", "Unit"]])
        uom_cat_id = uom_cat_ids[0] if uom_cat_ids else _execute(
            models, db, uid, password, "uom.category", "create", {"name": "Unit"}
        )
        uom_ids["PIECE"] = _execute(models, db, uid, password, "uom.uom", "create", {
            "name": "Unit",
            "category_id": uom_cat_id,
            "uom_type": "reference",
            "rounding": 1.0,
        })
        print(f"  PIECE → created 'Unit' (ID {uom_ids['PIECE']})")

    # Kilogram
    kg_ids = _execute(models, db, uid, password, "uom.uom", "search",
                      [["name", "in", ["kg", "Kg", "KG", "Kilogram(s)", "Kilogram"]]])
    if kg_ids:
        uom_ids["KG"] = kg_ids[0]
        name = _read(models, db, uid, password, "uom.uom",
                     [kg_ids[0]], ["name"])[0]["name"]
        print(f"  KG    → '{name}' (ID {kg_ids[0]})")
    else:
        uom_cat_ids = _execute(models, db, uid, password, "uom.category", "search",
                               [["name", "=", "Weight"]])
        uom_cat_id = uom_cat_ids[0] if uom_cat_ids else _execute(
            models, db, uid, password, "uom.category", "create", {"name": "Weight"}
        )
        uom_ids["KG"] = _execute(models, db, uid, password, "uom.uom", "create", {
            "name": "kg",
            "category_id": uom_cat_id,
            "uom_type": "reference",
            "rounding": 0.001,
        })
        print(f"  KG    → created 'kg' (ID {uom_ids['KG']})")

    return uom_ids


def create_products(models, db, uid, password,
                    pos_cat_ids, internal_cat_ids, uom_ids) -> list[dict]:
    print("\n[5/9] Creating products …")
    created_products = []

    # Check if pos_category_id field exists on product.template
    try:
        fields_info = models.execute_kw(
            db, uid, password, "product.template", "fields_get",
            [["pos_category_id"]], {"attributes": ["string"]}
        )
        has_pos_category = bool(fields_info)
    except Exception:
        has_pos_category = False

    for p in PRODUCTS:
        uom_id = uom_ids.get(p["unit_type"], uom_ids["PIECE"])
        pos_cat_id = pos_cat_ids.get(p["category"], False)
        internal_cat_id = internal_cat_ids.get(p["category"], False)

        # Check if product already exists by internal reference (SKU)
        existing = _execute(models, db, uid, password, "product.template", "search",
                            [["default_code", "=", p["sku"]]])
        if existing:
            product_tmpl_id = existing[0]
            print(f"  {p['sku']}: exists (template ID {product_tmpl_id})")
        else:
            vals = {
                "name": p["name"],
                "default_code": p["sku"],
                "barcode": p["barcode"],
                "list_price": p["price"],
                "standard_price": 0.0,
                "type": "consu",          # consumable — no stock tracking needed for demo
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "available_in_pos": True,
                "sale_ok": True,
                "purchase_ok": False,
            }
            if internal_cat_id:
                vals["categ_id"] = internal_cat_id
            if has_pos_category and pos_cat_id:
                vals["pos_category_id"] = pos_cat_id

            product_tmpl_id = _execute(models, db, uid, password,
                                       "product.template", "create", vals)
            print(f"  {p['sku']}: created (template ID {product_tmpl_id})")

        # Get the product.product variant ID
        variant_ids = _execute(models, db, uid, password, "product.product", "search",
                               [["product_tmpl_id", "=", product_tmpl_id]])
        variant_id = variant_ids[0] if variant_ids else None

        created_products.append({
            "name": p["name"],
            "sku": p["sku"],
            "barcode": p["barcode"],
            "category": p["category"],
            "unit_type": p["unit_type"],
            "price": p["price"],
            "odoo_template_id": product_tmpl_id,
            "odoo_product_id": variant_id,
        })

    return created_products


def create_payment_methods(models, db, uid, password) -> dict[str, int]:
    print("\n[6/9] Creating payment methods …")
    # In Odoo 17, pos.payment.method uses 'is_cash_count' for cash methods.
    methods = [
        {"name": "Cash", "is_cash_count": True},
        {"name": "Telebirr (Simulated)", "is_cash_count": False},
        {"name": "Chapa (Simulated)", "is_cash_count": False},
    ]
    method_ids: dict[str, int] = {}

    for m in methods:
        name = m["name"]
        existing = _execute(models, db, uid, password, "pos.payment.method", "search",
                            [["name", "=", name]])
        if existing:
            method_ids[name] = existing[0]
            print(f"  '{name}': exists (ID {existing[0]})")
        else:
            try:
                method_ids[name] = _execute(models, db, uid, password,
                                            "pos.payment.method", "create", m)
                print(f"  '{name}': created (ID {method_ids[name]})")
            except Exception as e:
                # Fallback: create with name only if extra fields cause issues
                try:
                    method_ids[name] = _execute(models, db, uid, password,
                                                "pos.payment.method", "create", {"name": name})
                    print(f"  '{name}': created with fallback (ID {method_ids[name]})")
                except Exception as e2:
                    print(f"  '{name}': FAILED — {e2}")

    return method_ids


def create_pos_config(models, db, uid, password, payment_method_ids) -> int:
    print("\n[7/9] Creating POS configuration …")
    pos_name = "Cashier Terminal 1"
    existing = _execute(models, db, uid, password, "pos.config", "search",
                        [["name", "=", pos_name]])
    if existing:
        pos_id = existing[0]
        print(f"  '{pos_name}': exists (ID {pos_id})")
    else:
        vals = {
            "name": pos_name,
            "payment_method_ids": [(6, 0, list(payment_method_ids.values()))],
        }
        try:
            pos_id = _execute(models, db, uid, password, "pos.config", "create", vals)
            print(f"  '{pos_name}': created (ID {pos_id})")
        except Exception as e:
            # Fallback: create with name only, then update payment methods
            pos_id = _execute(models, db, uid, password, "pos.config", "create",
                              {"name": pos_name})
            try:
                _execute(models, db, uid, password, "pos.config", "write",
                         [pos_id],
                         {"payment_method_ids": [(6, 0, list(payment_method_ids.values()))]})
            except Exception:
                pass
            print(f"  '{pos_name}': created with fallback (ID {pos_id})")
    return pos_id


def create_users(models, db, uid, password) -> dict[str, int]:
    print("\n[8/9] Creating users …")
    user_ids: dict[str, int] = {}

    # Cashier user
    cashier_login = "cashier"
    existing = _execute(models, db, uid, password, "res.users", "search",
                        [["login", "=", cashier_login]])
    if existing:
        user_ids["cashier"] = existing[0]
        print(f"  cashier: exists (ID {existing[0]})")
    else:
        # Find POS User group
        pos_user_group = _execute(models, db, uid, password, "res.groups", "search",
                                  [["full_name", "ilike", "Point of Sale / User"]])
        group_ids = pos_user_group if pos_user_group else []

        vals = {
            "name": "Demo Cashier",
            "login": cashier_login,
            "password": "cashier123",
            "email": "cashier@retaildemo.et",
            "groups_id": [(6, 0, group_ids)],
        }
        user_ids["cashier"] = _execute(models, db, uid, password, "res.users", "create", vals)
        print(f"  cashier: created (ID {user_ids['cashier']}, login: cashier, password: cashier123)")

    # Admin user already exists as uid=1 (admin), just confirm
    user_ids["admin"] = uid
    print(f"  admin: built-in admin user (ID {uid}, login: admin, password: admin)")

    return user_ids


def print_summary(url, db, created_products, payment_method_ids, pos_id, user_ids) -> None:
    print("\n" + "=" * 70)
    print("  ODOO SETUP COMPLETE")
    print("=" * 70)
    print(f"\n  URL:      {url}")
    print(f"  Database: {db}")
    print(f"\n  Admin login:    admin / admin")
    print(f"  Cashier login:  cashier / cashier123")
    print(f"\n  POS Config:     'Cashier Terminal 1' (ID {pos_id})")
    print(f"\n  Payment Methods:")
    for name, mid in payment_method_ids.items():
        print(f"    - {name} (ID {mid})")
    print(f"\n  Products ({len(created_products)} total):")
    print(f"  {'SKU':<22} {'Name':<25} {'Cat':<22} {'UoM':<6} {'Price':>8}  {'OdooID':>8}")
    print(f"  {'-'*22} {'-'*25} {'-'*22} {'-'*6} {'-'*8}  {'-'*8}")
    for p in created_products:
        print(
            f"  {p['sku']:<22} {p['name']:<25} {p['category']:<22} "
            f"{p['unit_type']:<6} {p['price']:>8.2f}  {str(p['odoo_product_id']):>8}"
        )
    print("\n  Next steps:")
    print("  1. Open http://localhost:8069 and log in as admin/admin")
    print("  2. Go to Point of Sale → Dashboard → Open 'Cashier Terminal 1'")
    print("  3. Run: python scripts/export_odoo_ids.py  (to sync IDs to Django)")
    print("=" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Odoo for the retail demo.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--password", default=DEFAULT_MASTER_PASSWORD,
                        help="Odoo master password")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    db = args.db
    master_password = args.password

    _wait_for_odoo(url)
    _ensure_db(url, db, master_password)

    print(f"\nConnecting to {url} / db={db} as admin …")
    common, models, uid = _login(url, db, ADMIN_USER, ADMIN_PASSWORD)
    print(f"Authenticated as admin (uid={uid})")

    install_modules(models, db, uid, ADMIN_PASSWORD)
    configure_company(models, db, uid, ADMIN_PASSWORD)
    pos_cat_ids, internal_cat_ids = create_product_categories(models, db, uid, ADMIN_PASSWORD)
    uom_ids = get_uom_ids(models, db, uid, ADMIN_PASSWORD)
    created_products = create_products(models, db, uid, ADMIN_PASSWORD,
                                       pos_cat_ids, internal_cat_ids, uom_ids)
    payment_method_ids = create_payment_methods(models, db, uid, ADMIN_PASSWORD)
    pos_id = create_pos_config(models, db, uid, ADMIN_PASSWORD, payment_method_ids)
    user_ids = create_users(models, db, uid, ADMIN_PASSWORD)

    print_summary(url, db, created_products, payment_method_ids, pos_id, user_ids)


if __name__ == "__main__":
    main()
