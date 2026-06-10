from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("internal_reference", "provider", "amount", "currency", "status", "customer_phone", "created_at")
    search_fields = ("internal_reference", "external_reference", "customer_phone")
    list_filter = ("provider", "status", "currency")
