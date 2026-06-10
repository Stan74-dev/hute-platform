from django.urls import path
from .views import owner_mobile_dashboard

urlpatterns = [path("owner-mobile-dashboard/", owner_mobile_dashboard)]
