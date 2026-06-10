from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MobileMoneyRequestViewSet, initiate_mobile_money, provider_callback
router=DefaultRouter(); router.register("requests", MobileMoneyRequestViewSet, basename="mobilemoney-request")
urlpatterns=[path("",include(router.urls)), path("initiate/",initiate_mobile_money), path("callback/<str:internal_reference>/",provider_callback)]
