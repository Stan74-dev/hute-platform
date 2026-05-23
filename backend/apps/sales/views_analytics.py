import csv
from decimal import Decimal
from io import StringIO

from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.http import HttpResponse
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sales.models import Sale, SaleItem


def money(value):
    return str(value or Decimal("0.00"))


def get_date_range(range_value):
    today = timezone.localdate()

    if range_value == "today":
        return today, today

    if range_value == "7d":
        return today - timezone.timedelta(days=6), today

    if range_value == "30d":
        return today - timezone.timedelta(days=29), today

    if range_value == "90d":
        return today - timezone.timedelta(days=89), today

    if range_value == "month":
        start = today.replace(day=1)
        return start, today

    return today, today


class SalesAnalyticsDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_value = (request.GET.get("range") or "today").strip().lower()
        warehouse_id = (request.GET.get("warehouse") or "").strip()

        date_from, date_to = get_date_range(range_value)

        sales = Sale.objects.select_related("warehouse").filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        if warehouse_id and warehouse_id != "all":
            sales = sales.filter(warehouse_id=warehouse_id)

        sale_items = SaleItem.objects.select_related("product", "sale", "sale__warehouse").filter(
            sale__in=sales
        )

        total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        total_profit = sales.aggregate(total=Sum("total_profit"))["total"] or Decimal("0.00")
        transactions = sales.count()
        average_sale = total_sales / transactions if transactions else Decimal("0.00")

        top_products = (
            sale_items.values("product_id", "product__name", "product__sku")
            .annotate(
                qty_sold=Sum("quantity"),
                revenue=Sum("line_total"),
                profit=Sum("line_profit"),
            )
            .order_by("-qty_sold", "-revenue")[:10]
        )

        warehouse_breakdown = (
            sales.values("warehouse_id", "warehouse__name")
            .annotate(
                sales_total=Sum("total_amount"),
                profit_total=Sum("total_profit"),
                transaction_count=Count("id"),
            )
            .order_by("-sales_total")
        )

        dashboard = {
            "summary": {
                "range": range_value,
                "date_from": str(date_from),
                "date_to": str(date_to),
                "total_sales": money(total_sales),
                "total_profit": money(total_profit),
                "transactions": transactions,
                "average_sale": money(average_sale),
            },
            "top_products": [
                {
                    "product_id": row["product_id"],
                    "product_name": row["product__name"] or "",
                    "sku": row["product__sku"] or "",
                    "qty_sold": row["qty_sold"] or 0,
                    "revenue": money(row["revenue"]),
                    "profit": money(row["profit"]),
                }
                for row in top_products
            ],
            "warehouse_breakdown": [
                {
                    "warehouse_id": row["warehouse_id"],
                    "warehouse_name": row["warehouse__name"] or "",
                    "sales": money(row["sales_total"]),
                    "profit": money(row["profit_total"]),
                    "transactions": row["transaction_count"] or 0,
                }
                for row in warehouse_breakdown
            ],
        }

        return Response(dashboard)


class SalesAnalyticsExportSummaryCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard = SalesAnalyticsDashboardView().get(request).data
        summary = dashboard.get("summary", {})

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_analytics_summary.csv"'

        writer = csv.writer(response)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Range", summary.get("range", "")])
        writer.writerow(["Date From", summary.get("date_from", "")])
        writer.writerow(["Date To", summary.get("date_to", "")])
        writer.writerow(["Total Sales", summary.get("total_sales", "0.00")])
        writer.writerow(["Total Profit", summary.get("total_profit", "0.00")])
        writer.writerow(["Transactions", summary.get("transactions", 0)])
        writer.writerow(["Average Sale", summary.get("average_sale", "0.00")])

        return response


class SalesAnalyticsExportTransactionsCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_value = (request.GET.get("range") or "today").strip().lower()
        warehouse_id = (request.GET.get("warehouse") or "").strip()

        date_from, date_to = get_date_range(range_value)

        sales = Sale.objects.select_related("warehouse", "cashier").filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        if warehouse_id and warehouse_id != "all":
            sales = sales.filter(warehouse_id=warehouse_id)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_transactions.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Receipt Number",
            "Date",
            "Cashier",
            "Warehouse",
            "Payment Method",
            "Subtotal",
            "Tax",
            "Grand Total",
            "Profit",
            "Terminal ID",
            "Terminal Name",
        ])

        for sale in sales.order_by("-created_at"):
            writer.writerow([
                sale.receipt_number,
                sale.created_at,
                sale.cashier.username if sale.cashier else "",
                sale.warehouse.name if sale.warehouse else "",
                sale.payment_method,
                money(sale.subtotal),
                money(sale.tax_total),
                money(sale.grand_total),
                money(sale.total_profit),
                sale.terminal_id,
                sale.terminal_name,
            ])

        return response


class SalesAnalyticsExportTopProductsCsvView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_value = (request.GET.get("range") or "today").strip().lower()
        warehouse_id = (request.GET.get("warehouse") or "").strip()

        date_from, date_to = get_date_range(range_value)

        sales = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        if warehouse_id and warehouse_id != "all":
            sales = sales.filter(warehouse_id=warehouse_id)

        sale_items = SaleItem.objects.select_related("product").filter(sale__in=sales)

        top_products = (
            sale_items.values("product_id", "product__name", "product__sku")
            .annotate(
                qty_sold=Sum("quantity"),
                revenue=Sum("line_total"),
                profit=Sum("line_profit"),
            )
            .order_by("-qty_sold", "-revenue")
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_top_products.csv"'

        writer = csv.writer(response)
        writer.writerow(["Product", "SKU", "Qty Sold", "Revenue", "Profit"])

        for row in top_products:
            writer.writerow([
                row["product__name"] or "",
                row["product__sku"] or "",
                row["qty_sold"] or 0,
                money(row["revenue"]),
                money(row["profit"]),
            ])

        return response