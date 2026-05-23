from rest_framework import serializers

from .models import SupplierInvoice, SupplierPayment


class SupplierInvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    po_number = serializers.CharField(source="purchase_order.po_number", read_only=True)
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = SupplierInvoice
        fields = [
            "id",
            "invoice_number",
            "supplier",
            "supplier_name",
            "purchase_order",
            "po_number",
            "warehouse_name",
            "invoice_date",
            "due_date",
            "total_amount",
            "amount_paid",
            "balance_due",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]

    def get_warehouse_name(self, obj):
        if obj.purchase_order and obj.purchase_order.warehouse:
            return obj.purchase_order.warehouse.name
        return ""


class SupplierPaymentSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = SupplierPayment
        fields = [
            "id",
            "payment_number",
            "invoice",
            "invoice_number",
            "supplier",
            "supplier_name",
            "payment_date",
            "amount",
            "payment_method",
            "reference",
            "notes",
            "created_by",
            "created_by_username",
            "created_at",
        ]


class SupplierPaymentCreateSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=SupplierPayment.METHOD_CHOICES)
    payment_date = serializers.DateField(required=False)
    reference = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)