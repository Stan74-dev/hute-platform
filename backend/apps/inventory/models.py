from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reorder_level = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    tax_rate = models.ForeignKey(
        "finance.TaxRate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_records")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_records")
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "warehouse")
        ordering = ["warehouse__name", "product__name"]

    def __str__(self):
        return f"{self.product} @ {self.warehouse} = {self.quantity}"


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_PARTIAL = "partial"
    STATUS_RECEIVED = "received"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.po_number

    @property
    def total_amount(self):
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.line_total
        return total

    @property
    def ordered_quantity_total(self):
        return sum(int(item.quantity or 0) for item in self.items.all())

    @property
    def received_quantity_total(self):
        return sum(int(item.received_quantity or 0) for item in self.items.all())

    @property
    def pending_quantity_total(self):
        pending = self.ordered_quantity_total - self.received_quantity_total
        return pending if pending > 0 else 0

    def refresh_status_from_items(self, save=True):
        if self.status == self.STATUS_CANCELLED:
            return self.status

        ordered_total = self.ordered_quantity_total
        received_total = self.received_quantity_total

        if ordered_total <= 0:
            new_status = self.STATUS_DRAFT
        elif received_total <= 0:
            new_status = self.STATUS_SUBMITTED
        elif received_total < ordered_total:
            new_status = self.STATUS_PARTIAL
        else:
            new_status = self.STATUS_RECEIVED

        self.status = new_status

        if save:
            self.save(update_fields=["status"])

        return new_status


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase_order_items")
    quantity = models.PositiveIntegerField(default=1)
    received_quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.name}"

    @property
    def pending_quantity(self):
        pending = int(self.quantity or 0) - int(self.received_quantity or 0)
        return pending if pending > 0 else 0

    @property
    def line_total(self):
        return Decimal(self.quantity or 0) * Decimal(self.unit_cost or 0)


class GoodsReceivedNote(models.Model):
    grn_number = models.CharField(max_length=100, unique=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="goods_received_notes",
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goods_received_notes_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.grn_number

    @property
    def total_received_quantity(self):
        return sum(int(item.quantity_received or 0) for item in self.items.all())


class GoodsReceivedNoteItem(models.Model):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="items")
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name="grn_items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="grn_items")
    batch_number = models.CharField(max_length=100, blank=True, default="")
    expiry_date = models.DateField(null=True, blank=True)
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.grn.grn_number} - {self.product.name}"

    @property
    def line_total(self):
        return Decimal(self.quantity_received or 0) * Decimal(self.unit_cost or 0)


class StockBatch(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_NEAR_EXPIRY = "near_expiry"
    STATUS_EXPIRED = "expired"
    STATUS_QUARANTINED = "quarantined"
    STATUS_WRITTEN_OFF = "written_off"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_NEAR_EXPIRY, "Near Expiry"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_QUARANTINED, "Quarantined"),
        (STATUS_WRITTEN_OFF, "Written Off"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_batches")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_batches")
    grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_batches",
    )
    grn_item = models.ForeignKey(
        GoodsReceivedNoteItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_batches",
    )
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_batches",
    )
    batch_number = models.CharField(max_length=100)
    received_date = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField(null=True, blank=True)
    quantity_received = models.PositiveIntegerField(default=0)
    quantity_available = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expiry_date", "created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.batch_number} - {self.warehouse.name}"

    def refresh_status(self, save=True):
        if self.status in [self.STATUS_QUARANTINED, self.STATUS_WRITTEN_OFF]:
            if save:
                self.save(update_fields=["status"])
            return self.status

        today = timezone.localdate()

        if self.expiry_date and self.expiry_date < today:
            self.status = self.STATUS_EXPIRED
        elif self.expiry_date and (self.expiry_date - today).days <= 30:
            self.status = self.STATUS_NEAR_EXPIRY
        else:
            self.status = self.STATUS_ACTIVE

        if save:
            self.save(update_fields=["status"])

        return self.status


class StockTransfer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_transfers")
    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_transfers_out",
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_transfers_in",
    )
    quantity = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transfers_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name}: {self.from_warehouse.name} -> {self.to_warehouse.name}"