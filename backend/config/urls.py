from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/accounts/", include("apps.accounts.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/sales/", include("apps.sales.urls")),
    path("api/finance/", include("apps.finance.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/branches/", include("apps.branches.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/payments/", include("apps.payments.urls")),
]