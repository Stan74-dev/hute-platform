from rest_framework import serializers
from .models import Sale, SaleItem


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "quantity",
            "unit_price",
            "unit_cost",
            "line_total",
            "line_profit",
        ]


class SaleSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    cashier_username = serializers.CharField(source="cashier.username", read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "receipt_number",
            "warehouse",
            "warehouse_name",
            "cashier",
            "cashier_username",
            "payment_method",
            "total_amount",
            "total_cost",
            "total_profit",
            "created_at",
            "items",
        ]