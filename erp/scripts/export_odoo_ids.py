#!/usr/bin/env python3
"""
export_odoo_ids.py — Export Odoo product IDs to a JSON file for Django sync.

After running setup_odoo.py, run this script to produce:
    erp/data/odoo_product_ids.json

Django's RealOdooClient.sync_products() can read this file (or call the
XML-RPC endpoint directly) to populate Product.odoo_product_id fields.

Usage:
    python scripts/export_odoo_ids.py [--url URL] [--db DB]
"""

from __future__ import annotations

import argparse
import json
import sys
import xmlrpc.client
from pathlib import Path

DEFAULT_URL = "http://localhost:8069"
DEFAULT_DB = "odoo_retail"
ADMIN_PASSWORD = "admin"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "odoo_product_ids.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    url = args.url.rstrip("/")
    db = args.db

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, "admin", ADMIN_PASSWORD, {})
    if not uid:
        sys.exit("ERROR: Cannot authenticate. Is Odoo running and setup complete?")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    def execute(model, method, *args, **kwargs):
        return models.execute_kw(db, uid, ADMIN_PASSWORD, model, method, list(args), kwargs)

    # Fetch all products that have a default_code (SKU)
    product_ids = execute("product.product", "search",
                          [["default_code", "!=", False], ["active", "=", True]])
    products = models.execute_kw(db, uid, ADMIN_PASSWORD, "product.product", "read",
                                 [product_ids],
                                 {"fields": ["id", "name", "default_code", "barcode",
                                             "list_price", "uom_id", "product_tmpl_id"]})

    output = []
    for p in products:
        output.append({
            "odoo_product_id": str(p["id"]),
            "odoo_template_id": str(p["product_tmpl_id"][0]) if p.get("product_tmpl_id") else None,
            "sku": p.get("default_code") or "",
            "name": p.get("name") or "",
            "barcode": p.get("barcode") or "",
            "price": p.get("list_price", 0.0),
            "uom": p["uom_id"][1] if p.get("uom_id") else "",
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Exported {len(output)} products to {OUTPUT_FILE}")
    print("\nSample:")
    for item in output[:3]:
        print(f"  {item['sku']:<22} odoo_id={item['odoo_product_id']:<6} {item['name']}")


if __name__ == "__main__":
    main()
