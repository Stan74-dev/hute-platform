from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FiscalDeviceViewSet, FiscalInvoiceViewSet, fiscalise_sale
router = DefaultRouter()
router.register("devices", FiscalDeviceViewSet, basename="fiscal-device")
router.register("invoices", FiscalInvoiceViewSet, basename="fiscal-invoice")
urlpatterns = [path("", include(router.urls)), path("sale/<int:sale_id>/submit/", fiscalise_sale)]
