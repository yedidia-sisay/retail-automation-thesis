#!/usr/bin/env python3
"""
health_check.py — Quick check that Odoo is up and the database is configured.

Usage:
    python scripts/health_check.py [--url URL] [--db DB]
"""

from __future__ import annotations

import argparse
import sys
import xmlrpc.client

DEFAULT_URL = "http://localhost:8069"
DEFAULT_DB = "odoo_retail"
ADMIN_PASSWORD = "admin"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    url = args.url.rstrip("/")
    db = args.db

    print(f"Checking Odoo at {url} …")

    # Version check
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        version = common.version()
        print(f"  Odoo version: {version.get('server_version', 'unknown')}")
    except Exception as e:
        sys.exit(f"  ERROR: Cannot reach Odoo — {e}")

    # Auth check
    uid = common.authenticate(db, "admin", ADMIN_PASSWORD, {})
    if not uid:
        print(f"  WARNING: Cannot authenticate to db='{db}'. Run setup_odoo.py first.")
        return

    print(f"  Auth OK (admin uid={uid})")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    def execute(model, method, *args, **kwargs):
        return models.execute_kw(db, uid, ADMIN_PASSWORD, model, method, list(args), kwargs)

    # Product count
    product_count = execute("product.template", "search_count", [["available_in_pos", "=", True]])
    print(f"  POS products: {product_count}")

    # POS config
    pos_configs = models.execute_kw(db, uid, ADMIN_PASSWORD, "pos.config", "search_read",
                                    [[]], {"fields": ["name"], "limit": 5})
    for cfg in pos_configs:
        print(f"  POS config: '{cfg['name']}'")

    # Payment methods
    pm = models.execute_kw(db, uid, ADMIN_PASSWORD, "pos.payment.method", "search_read",
                           [[]], {"fields": ["name"], "limit": 10})
    for m in pm:
        print(f"  Payment method: '{m['name']}'")

    print("\n  All checks passed.")


if __name__ == "__main__":
    main()
