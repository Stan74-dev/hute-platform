from django.contrib import admin

from .models import Sale, SaleItem, SaleItemBatchAllocation, Refund, RefundItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = (
        "product",
        "quantity",
        "unit_price",
        "unit_cost",
        "tax_rate_percent",
        "line_subtotal",
        "tax_amount",
        "line_total",
        "line_profit",
        "created_at",
    )
    can_delete = False


class SaleItemBatchAllocationInline(admin.TabularInline):
    model = SaleItemBatchAllocation
    extra = 0
    readonly_fields = ("sale_item", "stock_batch", "quantity_allocated", "created_at")
    can_delete = False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "warehouse",
        "cashier",
        "payment_method",
        "total_amount",
        "tax_amount",
        "total_profit",
        "created_at",
    )
    list_filter = ("payment_method", "warehouse", "created_at")
    search_fields = ("receipt_number", "cashier__username", "warehouse__name")
    readonly_fields = (
        "receipt_number",
        "warehouse",
        "cashier",
        "shift",
        "payment_method",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "total_profit",
        "terminal_id",
        "terminal_name",
        "created_at",
    )
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "product",
        "quantity",
        "unit_price",
        "tax_amount",
        "line_total",
        "line_profit",
        "created_at",
    )
    list_filter = ("created_at", "product")
    search_fields = ("sale__receipt_number", "product__name", "product__sku")
    readonly_fields = (
        "sale",
        "product",
        "quantity",
        "unit_price",
        "unit_cost",
        "tax_rate_percent",
        "line_subtotal",
        "tax_amount",
        "line_total",
        "line_profit",
        "created_at",
    )
    inlines = [SaleItemBatchAllocationInline]


@admin.register(SaleItemBatchAllocation)
class SaleItemBatchAllocationAdmin(admin.ModelAdmin):
    list_display = ("sale_item", "stock_batch", "quantity_allocated", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "sale_item__sale__receipt_number",
        "sale_item__product__name",
        "stock_batch__batch_number",
    )
    readonly_fields = ("sale_item", "stock_batch", "quantity_allocated", "created_at")


class RefundItemInline(admin.TabularInline):
    model = RefundItem
    extra = 0
    readonly_fields = (
        "sale_item",
        "product",
        "quantity",
        "unit_price",
        "unit_cost",
        "tax_rate_percent",
        "line_subtotal",
        "tax_amount",
        "line_total",
        "line_profit_reversed",
        "returned_to_stock",
        "created_at",
    )
    can_delete = False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "refund_number",
        "sale",
        "cashier",
        "payment_method",
        "total_amount",
        "tax_amount",
        "total_profit_reversed",
        "created_at",
    )
    list_filter = ("payment_method", "created_at")
    search_fields = ("refund_number", "sale__receipt_number", "cashier__username")
    readonly_fields = (
        "refund_number",
        "sale",
        "cashier",
        "payment_method",
        "reason",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "total_cost",
        "total_profit_reversed",
        "created_at",
    )
    inlines = [RefundItemInline]


@admin.register(RefundItem)
class RefundItemAdmin(admin.ModelAdmin):
    list_display = (
        "refund",
        "product",
        "quantity",
        "unit_price",
        "tax_amount",
        "line_total",
        "line_profit_reversed",
        "returned_to_stock",
        "created_at",
    )
    list_filter = ("returned_to_stock", "created_at", "product")
    search_fields = (
        "refund__refund_number",
        "refund__sale__receipt_number",
        "product__name",
        "product__sku",
    )
    readonly_fields = (
        "refund",
        "sale_item",
        "product",
        "quantity",
        "unit_price",
        "unit_cost",
        "tax_rate_percent",
        "line_subtotal",
        "tax_amount",
        "line_total",
        "line_profit_reversed",
        "returned_to_stock",
        "created_at",
    )