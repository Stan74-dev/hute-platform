from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.inventory.models import Product, Warehouse, StockBatch


class Sale(models.Model):
    PAYMENT_CASH = "cash"
    PAYMENT_CARD = "card"
    PAYMENT_ECOCASH = "ecocash"
    PAYMENT_BANK = "bank"
    PAYMENT_BANK_TRANSFER = "bank_transfer"

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_CARD, "Card"),
        (PAYMENT_ECOCASH, "EcoCash"),
        (PAYMENT_BANK, "Bank"),
        (PAYMENT_BANK_TRANSFER, "Bank Transfer"),
    ]

    receipt_number = models.CharField(max_length=80, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="sales")
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )

    shift = models.CharField(max_length=80, null=True, blank=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)

    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    terminal_id = models.CharField(max_length=120, blank=True, default="")
    terminal_name = models.CharField(max_length=120, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)

    @property
    def total_profit(self):
        return sum(Decimal(item.line_profit or 0) for item in self.items.all())

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.receipt_number


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    line_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        quantity = Decimal(self.quantity or 0)
        unit_price = Decimal(self.unit_price or 0)
        unit_cost = Decimal(self.unit_cost or 0)
        tax_rate = Decimal(self.tax_rate_percent or 0)

        self.line_subtotal = unit_price * quantity
        self.tax_amount = self.line_subtotal * (tax_rate / Decimal("100"))
        self.line_total = self.line_subtotal + self.tax_amount
        self.line_profit = (unit_price - unit_cost) * quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sale.receipt_number} - {self.product.name}"


class SaleItemBatchAllocation(models.Model):
    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.CASCADE,
        related_name="batch_allocations",
    )
    stock_batch = models.ForeignKey(
        StockBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_allocations",
    )
    quantity_allocated = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        batch_number = self.stock_batch.batch_number if self.stock_batch else "No batch"
        return f"{self.sale_item_id} - {batch_number} - {self.quantity_allocated}"


class Refund(models.Model):
    REFUND_CASH = "cash"
    REFUND_CARD = "card"
    REFUND_ECOCASH = "ecocash"
    REFUND_BANK = "bank"
    REFUND_STORE_CREDIT = "store_credit"

    REFUND_METHOD_CHOICES = [
        (REFUND_CASH, "Cash"),
        (REFUND_CARD, "Card"),
        (REFUND_ECOCASH, "EcoCash"),
        (REFUND_BANK, "Bank"),
        (REFUND_STORE_CREDIT, "Store Credit"),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="refunds")
    refund_number = models.CharField(max_length=80, unique=True)

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds",
    )

    payment_method = models.CharField(max_length=30, choices=REFUND_METHOD_CHOICES, default=REFUND_CASH)
    reason = models.TextField(blank=True, default="")

    subtotal_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_profit_reversed = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.refund_number


class RefundItem(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT, related_name="refund_items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="refund_items")

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    line_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_profit_reversed = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    returned_to_stock = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        quantity = Decimal(self.quantity or 0)
        unit_price = Decimal(self.unit_price or 0)
        unit_cost = Decimal(self.unit_cost or 0)
        tax_rate = Decimal(self.tax_rate_percent or 0)

        self.line_subtotal = unit_price * quantity
        self.tax_amount = self.line_subtotal * (tax_rate / Decimal("100"))
        self.line_total = self.line_subtotal + self.tax_amount
        self.line_profit_reversed = (unit_price - unit_cost) * quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.refund.refund_number} - {self.product.name}"