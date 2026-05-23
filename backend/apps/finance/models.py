from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.inventory.models import PurchaseOrder, Supplier


class SupplierInvoice(models.Model):
    STATUS_UNPAID = "unpaid"
    STATUS_PARTIAL = "partial"
    STATUS_PAID = "paid"
    STATUS_OVERDUE = "overdue"

    STATUS_CHOICES = [
        (STATUS_UNPAID, "Unpaid"),
        (STATUS_PARTIAL, "Partially Paid"),
        (STATUS_PAID, "Paid"),
        (STATUS_OVERDUE, "Overdue"),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="finance_invoices",
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finance_invoices",
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number

    def recalculate(self):
        subtotal_amount = Decimal(self.subtotal_amount or 0)
        tax_amount = Decimal(self.tax_amount or 0)
        total_amount = Decimal(self.total_amount or 0)
        amount_paid = Decimal(self.amount_paid or 0)

        if total_amount <= Decimal("0.00"):
            total_amount = subtotal_amount + tax_amount

        if amount_paid < 0:
            amount_paid = Decimal("0.00")

        if amount_paid > total_amount:
            amount_paid = total_amount

        balance_due = total_amount - amount_paid

        today = timezone.localdate()
        is_past_due = bool(self.due_date and self.due_date < today and balance_due > 0)

        if balance_due <= Decimal("0.00"):
            status = self.STATUS_PAID
            balance_due = Decimal("0.00")
        elif amount_paid > Decimal("0.00"):
            status = self.STATUS_PARTIAL
        else:
            status = self.STATUS_UNPAID

        if is_past_due and status != self.STATUS_PAID:
            status = self.STATUS_OVERDUE

        self.subtotal_amount = subtotal_amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        self.amount_paid = amount_paid
        self.balance_due = balance_due
        self.status = status

    def save(self, *args, **kwargs):
        self.recalculate()
        super().save(*args, **kwargs)

    def apply_payment(self, amount):
        amount = Decimal(amount or 0)
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        if amount > self.balance_due:
            raise ValueError("Payment amount cannot exceed balance due.")

        self.amount_paid = Decimal(self.amount_paid or 0) + amount
        self.save(update_fields=["amount_paid", "balance_due", "status", "updated_at"])


class SupplierPayment(models.Model):
    METHOD_CASH = "cash"
    METHOD_BANK = "bank_transfer"
    METHOD_ECOCASH = "ecocash"
    METHOD_CARD = "card"
    METHOD_OTHER = "other"

    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_BANK, "Bank Transfer"),
        (METHOD_ECOCASH, "EcoCash"),
        (METHOD_CARD, "Card"),
        (METHOD_OTHER, "Other"),
    ]

    invoice = models.ForeignKey(
        SupplierInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="finance_payments",
    )
    payment_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default=METHOD_BANK)
    reference = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supplier_payments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.payment_number