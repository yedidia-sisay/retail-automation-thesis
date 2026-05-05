from rest_framework import serializers

from apps.catalog.models import Category, DetectionClassMapping, Product, ProductBarcode


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        )


class ProductBarcodeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductBarcode
        fields = (
            "id",
            "product",
            "product_name",
            "barcode",
            "is_primary",
            "created_at",
        )


class DetectionClassMappingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = DetectionClassMapping
        fields = (
            "id",
            "class_name",
            "product",
            "product_name",
            "minimum_confidence",
            "is_active",
            "created_at",
            "updated_at",
        )


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    barcodes = ProductBarcodeSerializer(many=True, read_only=True)
    detection_mappings = DetectionClassMappingSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_name",
            "name",
            "sku",
            "unit_type",
            "current_price",
            "description",
            "image",
            "is_active",
            "barcodes",
            "detection_mappings",
            "odoo_product_id",
            "last_synced_at",
            "sync_status",
            "created_at",
            "updated_at",
        )
