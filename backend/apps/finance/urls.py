from django.urls import path

from .views import (
    FinanceDashboardView,
    SupplierInvoiceListView,
    SupplierPaymentListView,
    SupplierPaymentCreateView,
    SupplierInvoicePdfView,
    FinanceExportInvoicesCsvView,
    FinanceExportPaymentsCsvView,
    FinanceExportSummaryCsvView,
)
from .views_tax import (
    TaxRateListView,
    TaxSummaryView,
)

urlpatterns = [
    path("dashboard/", FinanceDashboardView.as_view()),

    path("invoices/", SupplierInvoiceListView.as_view()),
    path("payments/", SupplierPaymentListView.as_view()),
    path("payments/create/", SupplierPaymentCreateView.as_view()),

    path("invoices/<int:invoice_id>/pdf/", SupplierInvoicePdfView.as_view()),

    path("export/invoices.csv", FinanceExportInvoicesCsvView.as_view()),
    path("export/payments.csv", FinanceExportPaymentsCsvView.as_view()),
    path("export/summary.csv", FinanceExportSummaryCsvView.as_view()),

    path("tax-rates/", TaxRateListView.as_view()),
    path("tax-summary/", TaxSummaryView.as_view()),
]