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

        products = [
            {
                "name": "Coca Cola 500ml",
                "sku": "COCA-500ML",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("35.00"),
                "barcode": "100000000001",
                "class_name": "coca_cola_500ml",
            },
            {
                "name": "Pepsi 500ml",
                "sku": "PEPSI-500ML",
                "category_slug": "beverages",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("33.00"),
                "barcode": "100000000002",
                "class_name": "pepsi_500ml",
            },
            {
                "name": "Moya Vegetable Oil 1L",
                "sku": "MOYA-OIL-1L",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("420.00"),
                "barcode": "100000000003",
                "class_name": "moya_oil_1l",
            },
            {
                "name": "Pasta 500g",
                "sku": "PASTA-500G",
                "category_slug": "packaged-products",
                "unit_type": Product.UnitType.PIECE,
                "current_price": Decimal("95.00"),
                "barcode": "100000000004",
                "class_name": "pasta_500g",
            },
            {
                "name": "Banana",
                "sku": "BANANA-KG",
                "category_slug": "weighted-products",
                "unit_type": Product.UnitType.KG,
                "current_price": Decimal("80.00"),
                "barcode": None,
                "class_name": "banana",
            },
            {
                "name": "Tomato",
                "sku": "TOMATO-KG",
                "category_slug": "weighted-products",
                "unit_type": Product.UnitType.KG,
                "current_price": Decimal("70.00"),
                "barcode": None,
                "class_name": "tomato",
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
