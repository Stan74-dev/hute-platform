from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_warehouses = serializers.IntegerField()
    total_stock_units = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=14, decimal_places=2)