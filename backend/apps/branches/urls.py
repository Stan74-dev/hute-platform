from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, BranchTerminalViewSet

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")
router.register("terminals", BranchTerminalViewSet, basename="branch-terminal")

urlpatterns = [path("", include(router.urls))]
