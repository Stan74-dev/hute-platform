from django.contrib import admin

from .models import SupplierInvoice, SupplierPayment
from .models_tax import TaxRate


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "rate_percent",
        "tax_type",
        "category",
        "is_active",
        "is_default",
    )
    list_filter = ("tax_type", "category", "is_active", "is_default")
    search_fields = ("name", "code")


@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "supplier",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "amount_paid",
        "balance_due",
        "status",
        "due_date",
    )
    search_fields = ("invoice_number", "supplier__name")
    list_filter = ("status",)
    fields = (
        "supplier",
        "purchase_order",
        "invoice_number",
        "invoice_date",
        "due_date",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "amount_paid",
        "status",
        "notes",
    )


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number",
        "supplier",
        "amount",
        "payment_method",
        "payment_date",
    )
    search_fields = ("payment_number", "supplier__name")
    list_filter = ("payment_method",)