from django.contrib import admin

from apps.catalog.models import Category, DetectionClassMapping, Product, ProductBarcode


class ProductBarcodeInline(admin.TabularInline):
	model = ProductBarcode
	extra = 0


class DetectionClassMappingInline(admin.TabularInline):
	model = DetectionClassMapping
	extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "slug", "created_at", "updated_at")
	search_fields = ("name", "slug")
	prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"sku",
		"category",
		"unit_type",
		"current_price",
		"is_active",
		"sync_status",
		"odoo_product_id",
		"updated_at",
	)
	list_filter = ("category", "unit_type", "is_active", "sync_status")
	search_fields = (
		"name",
		"sku",
		"odoo_product_id",
		"category__name",
		"barcodes__barcode",
	)
	list_select_related = ("category",)
	inlines = (ProductBarcodeInline, DetectionClassMappingInline)


@admin.register(ProductBarcode)
class ProductBarcodeAdmin(admin.ModelAdmin):
	list_display = ("barcode", "product", "is_primary", "created_at")
	search_fields = ("barcode", "product__name", "product__sku")
	list_filter = ("is_primary",)
	list_select_related = ("product",)


@admin.register(DetectionClassMapping)
class DetectionClassMappingAdmin(admin.ModelAdmin):
	list_display = ("class_name", "product", "minimum_confidence", "is_active", "updated_at")
	search_fields = ("class_name", "product__name", "product__sku")
	list_filter = ("is_active",)
	list_select_related = ("product",)
