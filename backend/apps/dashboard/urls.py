from django.urls import path

from .views import (
    ExecutiveDashboardView,
    ExecutiveDashboardV2View,
    DayDetailView,
    HistoricalTrendsView,
)

urlpatterns = [
    path("", ExecutiveDashboardView.as_view()),
    path("executive-v2/", ExecutiveDashboardV2View.as_view()),
    path("day-detail/", DayDetailView.as_view()),
    path("historical-trends/", HistoricalTrendsView.as_view()),
]