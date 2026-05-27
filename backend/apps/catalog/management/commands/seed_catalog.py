from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, DetectionClassMapping, Product, ProductBarcode


class Command(BaseCommand):
    help = "Seed demo catalog data (categories, products, barcodes, detection mappings)."

    def handle(self, *args, **options):
        categories = {
            "packaged-products": {
                "name": "Packaged Products",
                "description": "Packaged items sold per piece (bottles, boxes, etc).",
            },
            "beverages": {
                "name": "Beverages",
                "description": "Drinks and beverages sold per piece.",
            },
            "weighted-products": {
                "name": "Weighted Products",
                "description": "Items sold by weight (fruits, vegetables).",
            },
        }

        category_objs: dict[str, Category] = {}
        for slug, data in categories.items():
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                },
            )
            category_objs[slug] = category

        # Products keyed to the exact class names the YOLO model returns.
        # class_name must match model.names[i] exactly (case-sensitive).
        products = [
            # ── Beverages ──────────────────────────────────────────────────
            {
                "name": "Coca Cola",
                "sku": "COCA-COLA",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("35.00"),
                "barcode": "100000000001",
                "class_name": "Coca Cola",
            },
            {
                "name": "Pepsi",
                "sku": "PEPSI",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("33.00"),
                "barcode": "100000000002",
                "class_name": "Pepsi",
            },
            {
                "name": "Sol Water",
                "sku": "SOL-WATER",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("25.00"),
                "barcode": "100000000010",
                "class_name": "Sol Water",
            },
            {
                "name": "Cappuccino",
                "sku": "CAPPUCCINO",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("45.00"),
                "barcode": "100000000011",
                "class_name": "Cappuccino",
            },
            # ── Packaged Products ──────────────────────────────────────────
            {
                "name": "Dove Soap",
                "sku": "DOVE-SOAP",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("85.00"),
                "barcode": "100000000003",
                "class_name": "Dove Soap",
            },
            {
                "name": "Duru Soap",
                "sku": "DURU-SOAP",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("75.00"),
                "barcode": "100000000004",
                "class_name": "Duru Soap",
            },
            {
                "name": "Mawell Pasta",
                "sku": "MAWELL-PASTA",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("95.00"),
                "barcode": "100000000005",
                "class_name": "Mawell Pasta",
            },
            {
                "name": "Omaar Tuna",
                "sku": "OMAAR-TUNA",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("120.00"),
                "barcode": "100000000006",
                "class_name": "Omaar Tuna",
            },
            {
                "name": "Abounded Biscuit",
                "sku": "ABOUNDED-BISCUIT",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("55.00"),
                "barcode": "100000000007",
                "class_name": "Abounded Biscuit",
            },
            {
                "name": "Nice Small Soft",
                "sku": "NICE-SMALL-SOFT",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("40.00"),
                "barcode": "100000000008",
                "class_name": "Nice Small Soft",
            },
            {
                "name": "Bravo Tissue Paper",
                "sku": "BRAVO-TISSUE",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("65.00"),
                "barcode": "100000000009",
                "class_name": "Bravo Tissue Paper",
            },
            {
                "name": "Eve Comfort",
                "sku": "EVE-COMFORT",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("110.00"),
                "barcode": "100000000012",
                "class_name": "Eve Comfort",
            },
            {
                "name": "Detergent",
                "sku": "DETERGENT",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("130.00"),
                "barcode": "100000000013",
                "class_name": "detergent",
            },
            {
                "name": "Blue Sunchips",
                "sku": "BLUE-SUNCHIPS",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("50.00"),
                "barcode": "100000000014",
                "class_name": "Blue Sunchips",
            },
            {
                "name": "Yellow Sunchips",
                "sku": "YELLOW-SUNCHIPS",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("50.00"),
                "barcode": "100000000015",
                "class_name": "Yellow Sunchips",
            },
            {
                "name": "Red QQ Snack",
                "sku": "RED-QQ-SNACK",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("30.00"),
                "barcode": "100000000016",
                "class_name": "Red QQ snack",
            },
            {
                "name": "Decoy",
                "sku": "DECOY",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("20.00"),
                "barcode": "100000000017",
                "class_name": "Decoy",
            },
        ]

        created_products = 0
        created_barcodes = 0
        created_mappings = 0

        for p in products:
            category = category_objs[p["category_slug"]]
            product, product_created = Product.objects.update_or_create(
                sku=p["sku"],
                defaults={
                    "category": category,
                    "name": p["name"],
                    "unit_type": p["unit_type"],
                    "current_price": p["current_price"],
                    "description": "",
                    "is_active": True,
                    "sync_status": Product.SyncStatus.LOCAL_ONLY,
                    "odoo_product_id": "",
                    "last_synced_at": None,
                },
            )
            if product_created:
                created_products += 1

            if p["barcode"]:
                _, barcode_created = ProductBarcode.objects.update_or_create(
                    barcode=p["barcode"],
                    defaults={
                        "product": product,
                        "is_primary": True,
                    },
                )
                if barcode_created:
                    created_barcodes += 1

            _, mapping_created = DetectionClassMapping.objects.update_or_create(
                class_name=p["class_name"],
                defaults={
                    "product": product,
                    "minimum_confidence": Decimal("0.70"),
                    "is_active": True,
                },
            )
            if mapping_created:
                created_mappings += 1

        self.stdout.write(self.style.SUCCESS("Catalog seed complete."))
        self.stdout.write(
            f"Categories: {Category.objects.count()}, "
            f"Products: {Product.objects.count()} (+{created_products}), "
            f"Barcodes: {ProductBarcode.objects.count()} (+{created_barcodes}), "
            f"Mappings: {DetectionClassMapping.objects.count()} (+{created_mappings})"
        )
