from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.catalog.views import (
    CategoryViewSet,
    DetectionClassMappingViewSet,
    ProductBarcodeViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="catalog-category")
router.register(r"products", ProductViewSet, basename="catalog-product")
router.register(r"barcodes", ProductBarcodeViewSet, basename="catalog-barcode")
router.register(
    r"detection-mappings",
    DetectionClassMappingViewSet,
    basename="catalog-detection-mapping",
)

urlpatterns = [
    path("", include(router.urls)),
]
