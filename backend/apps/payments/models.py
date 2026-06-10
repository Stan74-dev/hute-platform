from decimal import Decimal
from django.conf import settings
from django.db import models

class PaymentTransaction(models.Model):
    PROVIDERS = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("ecocash", "EcoCash"),
        ("innbucks", "InnBucks"),
        ("mukuru", "Mukuru"),
        ("zipit", "ZIPIT"),
    ]
    STATUSES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    provider = models.CharField(max_length=30, choices=PROVIDERS)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="USD")
    customer_phone = models.CharField(max_length=40, blank=True)
    external_reference = models.CharField(max_length=120, blank=True)
    internal_reference = models.CharField(max_length=120, unique=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
