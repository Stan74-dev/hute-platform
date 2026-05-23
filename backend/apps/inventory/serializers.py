from rest_framework import serializers
from .models import (
    GoodsReceivedNote,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Stock,
    StockTransfer,
    Supplier,
    SupplierInvoice,
    SupplierPayment,
    Warehouse,
)


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    preferred_supplier_name = serializers.CharField(source="preferred_supplier.name", read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    reorder_level = serializers.IntegerField(source="product.reorder_level", read_only=True)

    class Meta:
        model = Stock
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "product",
            "product_name",
            "product_sku",
            "quantity",
            "reorder_level",
            "created_at",
            "updated_at",
        ]


class StockTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransfer
        fields = "__all__"


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "quantity",
            "unit_cost",
            "line_total",
            "created_at",
            "updated_at",
        ]


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    purchase_order_number = serializers.CharField(source="purchase_order.po_number", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = GoodsReceivedNote
        fields = [
            "id",
            "grn_number",
            "purchase_order",
            "purchase_order_number",
            "supplier",
            "supplier_name",
            "warehouse",
            "warehouse_name",
            "received_by",
            "notes",
            "created_at",
            "updated_at",
        ]


class SupplierPaymentSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)

    class Meta:
        model = SupplierPayment
        fields = [
            "id",
            "reference",
            "invoice",
            "invoice_number",
            "supplier",
            "supplier_name",
            "amount",
            "payment_date",
            "payment_method",
            "notes",
            "created_at",
            "updated_at",
        ]


class SupplierInvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    purchase_order_number = serializers.CharField(source="purchase_order.po_number", read_only=True)
    payments = SupplierPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = SupplierInvoice
        fields = [
            "id",
            "invoice_number",
            "purchase_order",
            "purchase_order_number",
            "supplier",
            "supplier_name",
            "invoice_date",
            "due_date",
            "total_amount",
            "amount_paid",
            "balance_due",
            "status",
            "notes",
            "payments",
            "created_at",
            "updated_at",
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    grn = GoodsReceivedNoteSerializer(read_only=True)
    supplier_invoice = SupplierInvoiceSerializer(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "supplier",
            "supplier_name",
            "warehouse",
            "warehouse_name",
            "status",
            "notes",
            "total_amount",
            "items",
            "grn",
            "supplier_invoice",
            "created_at",
            "updated_at",
        ]