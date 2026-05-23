from django.contrib import admin

from apps.accounts.utils import create_audit_log
from .models import (
    Product,
    Warehouse,
    Stock,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceivedNote,
    StockTransfer,
)


def _safe_user(request):
    return request.user if getattr(request.user, "is_authenticated", False) else None


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'barcode',
        'selling_price',
        'cost_price',
        'reorder_level',
        'is_active',
    )
    search_fields = ('name', 'sku', 'barcode')
    list_filter = ('is_active',)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='product_created' if is_new else 'product_updated',
            target_type='product',
            target_id=obj.id,
            description=(
                f'Created product {obj.name} from Django admin.'
                if is_new
                else f'Updated product {obj.name} from Django admin.'
            ),
            metadata={
                'product_id': obj.id,
                'name': obj.name,
                'sku': obj.sku,
                'barcode': obj.barcode,
                'selling_price': str(obj.selling_price),
                'cost_price': str(obj.cost_price),
                'reorder_level': obj.reorder_level,
                'is_active': obj.is_active,
                'source': 'django_admin',
            },
        )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location', 'is_active')
    search_fields = ('name', 'code', 'location')
    list_filter = ('is_active',)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='warehouse_created' if is_new else 'warehouse_updated',
            target_type='warehouse',
            target_id=obj.id,
            description=(
                f'Created warehouse {obj.name} from Django admin.'
                if is_new
                else f'Updated warehouse {obj.name} from Django admin.'
            ),
            metadata={
                'warehouse_id': obj.id,
                'name': obj.name,
                'code': obj.code,
                'location': obj.location,
                'is_active': obj.is_active,
                'source': 'django_admin',
            },
        )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity')
    search_fields = ('product__name', 'product__sku', 'warehouse__name')
    list_filter = ('warehouse',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    list_filter = ('is_active',)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='supplier_created' if is_new else 'supplier_updated',
            target_type='supplier',
            target_id=obj.id,
            description=(
                f'Created supplier {obj.name} from Django admin.'
                if is_new
                else f'Updated supplier {obj.name} from Django admin.'
            ),
            metadata={
                'supplier_id': obj.id,
                'name': obj.name,
                'contact_person': obj.contact_person,
                'email': obj.email,
                'phone': obj.phone,
                'address': obj.address,
                'is_active': obj.is_active,
                'source': 'django_admin',
            },
        )


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'warehouse', 'status', 'created_at')
    search_fields = ('po_number', 'supplier__name', 'warehouse__name')
    list_filter = ('status', 'warehouse', 'supplier')
    inlines = [PurchaseOrderItemInline]

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='purchase_order_created' if is_new else 'purchase_order_updated',
            target_type='purchase_order',
            target_id=obj.id,
            description=(
                f'Created purchase order {obj.po_number} from Django admin.'
                if is_new
                else f'Updated purchase order {obj.po_number} from Django admin.'
            ),
            metadata={
                'purchase_order_id': obj.id,
                'po_number': obj.po_number,
                'supplier_id': obj.supplier_id,
                'supplier_name': getattr(obj.supplier, 'name', ''),
                'warehouse_id': obj.warehouse_id,
                'warehouse_name': getattr(obj.warehouse, 'name', ''),
                'status': obj.status,
                'notes': obj.notes,
                'source': 'django_admin',
            },
        )


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = ('grn_number', 'purchase_order', 'created_at')
    search_fields = ('grn_number', 'purchase_order__po_number')

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='grn_created' if is_new else 'grn_updated',
            target_type='goods_received_note',
            target_id=obj.id,
            description=(
                f'Created GRN {obj.grn_number} from Django admin.'
                if is_new
                else f'Updated GRN {obj.grn_number} from Django admin.'
            ),
            metadata={
                'grn_id': obj.id,
                'grn_number': obj.grn_number,
                'purchase_order_id': obj.purchase_order_id,
                'purchase_order_number': getattr(obj.purchase_order, 'po_number', ''),
                'notes': obj.notes,
                'source': 'django_admin',
            },
        )


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('product', 'from_warehouse', 'to_warehouse', 'quantity', 'created_by', 'created_at')
    search_fields = (
        'product__name',
        'product__sku',
        'from_warehouse__name',
        'to_warehouse__name',
        'created_by__username',
    )
    list_filter = ('from_warehouse', 'to_warehouse')

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        create_audit_log(
            actor=_safe_user(request),
            action='stock_transfer_created' if is_new else 'stock_transfer_updated',
            target_type='stock_transfer',
            target_id=obj.id,
            description=(
                f'Created stock transfer #{obj.id} from Django admin.'
                if is_new
                else f'Updated stock transfer #{obj.id} from Django admin.'
            ),
            metadata={
                'stock_transfer_id': obj.id,
                'product_id': obj.product_id,
                'product_name': getattr(obj.product, 'name', ''),
                'from_warehouse_id': obj.from_warehouse_id,
                'from_warehouse_name': getattr(obj.from_warehouse, 'name', ''),
                'to_warehouse_id': obj.to_warehouse_id,
                'to_warehouse_name': getattr(obj.to_warehouse, 'name', ''),
                'quantity': obj.quantity,
                'created_by_id': obj.created_by_id,
                'created_by_username': getattr(obj.created_by, 'username', '') if obj.created_by else '',
                'source': 'django_admin',
            },
        )