from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CurrencyViewSet, ExchangeRateViewSet, SplitTenderViewSet, calculate_split_tender
router = DefaultRouter(); router.register("currencies", CurrencyViewSet); router.register("exchange-rates", ExchangeRateViewSet); router.register("split-tenders", SplitTenderViewSet)
urlpatterns = [path("", include(router.urls)), path("calculate-split/", calculate_split_tender)]
