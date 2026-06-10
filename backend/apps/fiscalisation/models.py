from django.conf import settings
from django.db import models

class FiscalProvider(models.TextChoices):
    ZIMRA_FDMS = "zimra_fdms", "ZIMRA FDMS Direct"
    MIDDLEWARE = "middleware", "Fiscal Middleware"
    SYNVAS = "synvas", "Synvas Fiscbyte"
    OTHER = "other", "Other"

class FiscalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUBMITTED = "submitted", "Submitted"
    ACCEPTED = "accepted", "Accepted"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"

class FiscalDevice(models.Model):
    name = models.CharField(max_length=120)
    provider = models.CharField(max_length=40, choices=FiscalProvider.choices, default=FiscalProvider.MIDDLEWARE)
    device_id = models.CharField(max_length=120, blank=True)
    branch_code = models.CharField(max_length=40, blank=True)
    api_base_url = models.URLField(blank=True)
    api_key_label = models.CharField(max_length=120, blank=True, help_text="Store real keys in environment variables, not here.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class FiscalInvoice(models.Model):
    sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.SET_NULL, related_name="fiscal_invoices")
    invoice_number = models.CharField(max_length=120, unique=True)
    currency = models.CharField(max_length=10, default="USD")
    gross_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    buyer_name = models.CharField(max_length=160, blank=True)
    buyer_tax_number = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=30, choices=FiscalStatus.choices, default=FiscalStatus.PENDING)
    fiscal_day_number = models.CharField(max_length=80, blank=True)
    fiscal_receipt_number = models.CharField(max_length=120, blank=True)
    fiscal_signature = models.TextField(blank=True)
    fiscal_qr_data = models.TextField(blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.invoice_number

class FiscalSubmissionLog(models.Model):
    invoice = models.ForeignKey(FiscalInvoice, on_delete=models.CASCADE, related_name="submission_logs")
    status = models.CharField(max_length=30, choices=FiscalStatus.choices)
    message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
