from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.checkout.views import (
    AddBarcodeItemAPIView,
    AddWeightedItemAPIView,
    CheckoutItemViewSet,
    CheckoutSessionViewSet,
    ConfirmCheckoutAPIView,
)

router = DefaultRouter()
router.register(r"sessions", CheckoutSessionViewSet, basename="checkout-session")
router.register(r"items", CheckoutItemViewSet, basename="checkout-item")

urlpatterns = [
    path("sessions/<int:session_id>/confirm/", ConfirmCheckoutAPIView.as_view(), name="checkout-confirm"),
    path(
        "sessions/<int:session_id>/add-barcode/",
        AddBarcodeItemAPIView.as_view(),
        name="checkout-add-barcode",
    ),
    path(
        "sessions/<int:session_id>/add-weighted-item/",
        AddWeightedItemAPIView.as_view(),
        name="checkout-add-weighted-item",
    ),
    path("", include(router.urls)),
]
