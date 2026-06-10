from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet,TenantViewSet,SubscriptionViewSet,LicenseKeyViewSet,current_license_status
router=DefaultRouter(); router.register("plans",SubscriptionPlanViewSet); router.register("tenants",TenantViewSet); router.register("subscriptions",SubscriptionViewSet); router.register("license-keys",LicenseKeyViewSet)
urlpatterns=[path("",include(router.urls)), path("status/",current_license_status)]
