from django.urls import path

from apps.payments.views import PaymentDetailAPIView, SimulatePaymentAPIView

urlpatterns = [
	path("simulate/", SimulatePaymentAPIView.as_view(), name="payments-simulate"),
	path("<int:payment_id>/", PaymentDetailAPIView.as_view(), name="payments-detail"),
]
