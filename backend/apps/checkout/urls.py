from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.checkout.views import CheckoutItemViewSet, CheckoutSessionViewSet

router = DefaultRouter()
router.register(r"sessions", CheckoutSessionViewSet, basename="checkout-session")
router.register(r"items", CheckoutItemViewSet, basename="checkout-item")

urlpatterns = [
    path("", include(router.urls)),
]
