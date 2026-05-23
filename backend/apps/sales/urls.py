from django.urls import path

from .views import SaleListView, SaleDetailView, CheckoutView, SalesAnalyticsDashboardView
from .views_refunds import RefundListCreateView, RefundDetailView
from .views_refunds import RefundListCreateView, RefundDetailView

urlpatterns = [
    path("", SaleListView.as_view()),
    path("checkout/", CheckoutView.as_view()),
    path("analytics/dashboard/", SalesAnalyticsDashboardView.as_view()),
    path("<int:sale_id>/", SaleDetailView.as_view()),
    path("refunds/", RefundListCreateView.as_view()),
    path("refunds/<int:refund_id>/", RefundDetailView.as_view()),
    path("refunds/", RefundListCreateView.as_view()),
    path("refunds/<int:refund_id>/", RefundDetailView.as_view()),
]