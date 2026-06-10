from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentTransactionViewSet, initiate_payment

router = DefaultRouter()
router.register("transactions", PaymentTransactionViewSet, basename="payment-transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("initiate/", initiate_payment),
]
