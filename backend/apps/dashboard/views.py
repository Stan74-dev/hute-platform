from decimal import Decimal
from datetime import datetime, time, timedelta

from django.db.models import Sum, Count, F, DecimalField
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.finance.models import SupplierInvoice, SupplierPayment
from apps.inventory.models import PurchaseOrder, StockBatch
from apps.sales.models import Sale, SaleItem


def _parse_date_param(value):
    if not value:
        return timezone.localdate()
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return timezone.localdate()


def _day_range(target_date):
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)

    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt)

    return start_dt, end_dt


def _money(value):
    return str((Decimal(value or 0)).quantize(Decimal("0.01")))


def _sales_for_date(target_date):
    start_dt, end_dt = _day_range(target_date)
    return (
        Sale.objects
        .select_related("warehouse", "cashier")
        .prefetch_related("items__product", "items__batch_allocations__stock_batch")
        .filter(created_at__range=(start_dt, end_dt))
        .order_by("-created_at")
    )


def _sales_metrics(sales_qs):
    subtotal_amount = sales_qs.aggregate(total=Sum("subtotal_amount"))["total"] or Decimal("0.00")
    tax_amount = sales_qs.aggregate(total=Sum("tax_amount"))["total"] or Decimal("0.00")
    total_amount = sales_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    sale_items = SaleItem.objects.filter(sale__in=sales_qs)
    total_cost = sale_items.aggregate(
        total=Sum(
            F("unit_cost") * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["total"] or Decimal("0.00")

    total_profit = subtotal_amount - total_cost
    items_sold = sale_items.aggregate(total=Sum("quantity"))["total"] or 0

    return {
        "sales_count": sales_qs.count(),
        "transactions": sales_qs.count(),
        "items_sold": items_sold,
        "subtotal_amount": subtotal_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "total_sales": total_amount,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "average_sale": (total_amount / sales_qs.count()) if sales_qs.count() else Decimal("0.00"),
    }


def _serialize_sale_row(sale):
    total_cost = sum((Decimal(item.unit_cost or 0) * Decimal(item.quantity or 0)) for item in sale.items.all())
    profit = Decimal(sale.subtotal_amount or 0) - total_cost

    return {
        "id": sale.id,
        "receipt": sale.receipt_number,
        "receipt_number": sale.receipt_number,
        "cashier": sale.cashier.username if sale.cashier else "-",
        "cashier_username": sale.cashier.username if sale.cashier else "-",
        "warehouse": sale.warehouse.name if sale.warehouse else "-",
        "warehouse_name": sale.warehouse.name if sale.warehouse else "-",
        "shift": sale.shift,
        "payment": sale.payment_method,
        "payment_method": sale.payment_method,
        "subtotal": _money(sale.subtotal_amount),
        "subtotal_amount": _money(sale.subtotal_amount),
        "tax": _money(sale.tax_amount),
        "tax_amount": _money(sale.tax_amount),
        "total": _money(sale.total_amount),
        "total_amount": _money(sale.total_amount),
        "profit": _money(profit),
        "created": sale.created_at,
        "created_at": sale.created_at,
        "action": sale.id,
    }


def _serialize_product_summary(row):
    return {
        "product_id": row["product_id"],
        "product": row["product__name"] or "",
        "product_name": row["product__name"] or "",
        "sku": row["product__sku"] or "",
        "product_sku": row["product__sku"] or "",
        "quantity": row["quantity"] or 0,
        "qty_sold": row["quantity"] or 0,
        "subtotal": _money(row["subtotal"] or Decimal("0.00")),
        "subtotal_amount": _money(row["subtotal"] or Decimal("0.00")),
        "tax": _money(row["tax"] or Decimal("0.00")),
        "tax_amount": _money(row["tax"] or Decimal("0.00")),
        "total": _money(row["total"] or Decimal("0.00")),
        "total_amount": _money(row["total"] or Decimal("0.00")),
        "revenue": _money(row["total"] or Decimal("0.00")),
    }


class ExecutiveDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_for_date(target_date)
        metrics = _sales_metrics(sales_qs)

        anomaly_summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": 0,
        }

        shift_variance_summary = {
            "short": 0,
            "over": 0,
            "balanced": 0,
            "total": 0,
        }

        recent_priority_anomalies = []

        return Response({
            "date": str(target_date),

            # summary block
            "summary": {
                "sales_count": metrics["sales_count"],
                "transactions": metrics["transactions"],
                "items_sold": metrics["items_sold"],
                "subtotal_amount": _money(metrics["subtotal_amount"]),
                "tax_amount": _money(metrics["tax_amount"]),
                "total_amount": _money(metrics["total_amount"]),
                "total_sales": _money(metrics["total_sales"]),
                "total_cost": _money(metrics["total_cost"]),
                "total_profit": _money(metrics["total_profit"]),
                "average_sale": _money(metrics["average_sale"]),
                "closed_shifts": 0,
                "open_cases": 0,
                "breached_cases": 0,
                "escalated_cases": 0,
                "anomalies_today": anomaly_summary["total"],
            },

            # direct aliases for frontend pages that do not read summary
            "total_sales": _money(metrics["total_sales"]),
            "total_profit": _money(metrics["total_profit"]),
            "transactions": metrics["transactions"],
            "closed_shifts": 0,
            "open_cases": 0,
            "breached_cases": 0,
            "escalated_cases": 0,
            "anomalies_today": anomaly_summary["total"],

            "anomaly_summary": anomaly_summary,
            "shift_variance_summary": shift_variance_summary,
            "recent_priority_anomalies": recent_priority_anomalies,

            "recent_sales": [_serialize_sale_row(sale) for sale in sales_qs[:10]],
        })


class ExecutiveDashboardV2View(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_for_date(target_date)
        metrics = _sales_metrics(sales_qs)

        finance_invoices = SupplierInvoice.objects.all()
        finance_payments = SupplierPayment.objects.all()

        total_payables = finance_invoices.aggregate(total=Sum("balance_due"))["total"] or Decimal("0.00")
        total_invoiced = finance_invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        total_paid_to_suppliers = finance_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        overdue_invoices = finance_invoices.filter(due_date__lt=timezone.localdate()).exclude(
            status=getattr(SupplierInvoice, "STATUS_PAID", "paid")
        )
        overdue_amount = overdue_invoices.aggregate(total=Sum("balance_due"))["total"] or Decimal("0.00")

        po_qs = PurchaseOrder.objects.all()
        open_purchase_orders = po_qs.exclude(status=getattr(PurchaseOrder, "STATUS_RECEIVED", "received")).exclude(
            status=getattr(PurchaseOrder, "STATUS_CANCELLED", "cancelled")
        ).count()

        near_expiry_batches = StockBatch.objects.filter(
            status=getattr(StockBatch, "STATUS_NEAR_EXPIRY", "near_expiry"),
            quantity_available__gt=0,
        ).count()

        expired_batches = StockBatch.objects.filter(
            status=getattr(StockBatch, "STATUS_EXPIRED", "expired"),
            quantity_available__gt=0,
        ).count()

        payment_breakdown_qs = (
            sales_qs.values("payment_method")
            .annotate(count=Count("id"), total=Sum("total_amount"))
            .order_by("payment_method")
        )
        payment_breakdown = [
            {
                "payment_method": row["payment_method"],
                "count": row["count"] or 0,
                "transactions": row["count"] or 0,
                "total_amount": _money(row["total"] or Decimal("0.00")),
            }
            for row in payment_breakdown_qs
        ]

        warehouse_breakdown_qs = (
            sales_qs.values("warehouse_id", "warehouse__name")
            .annotate(count=Count("id"), total=Sum("total_amount"))
            .order_by("-total")
        )
        warehouse_breakdown = [
            {
                "warehouse_id": row["warehouse_id"],
                "warehouse": row["warehouse__name"] or "",
                "warehouse_name": row["warehouse__name"] or "",
                "transactions": row["count"] or 0,
                "sales_count": row["count"] or 0,
                "sales": _money(row["total"] or Decimal("0.00")),
                "total_amount": _money(row["total"] or Decimal("0.00")),
            }
            for row in warehouse_breakdown_qs
        ]

        return Response({
            "date": str(target_date),
            "summary": {
                "sales_count": metrics["sales_count"],
                "transactions": metrics["transactions"],
                "items_sold": metrics["items_sold"],
                "subtotal_amount": _money(metrics["subtotal_amount"]),
                "tax_amount": _money(metrics["tax_amount"]),
                "total_amount": _money(metrics["total_amount"]),
                "total_sales": _money(metrics["total_sales"]),
                "total_cost": _money(metrics["total_cost"]),
                "total_profit": _money(metrics["total_profit"]),
                "average_sale": _money(metrics["average_sale"]),
                "total_invoiced": _money(total_invoiced),
                "total_payables": _money(total_payables),
                "total_paid_to_suppliers": _money(total_paid_to_suppliers),
                "overdue_amount": _money(overdue_amount),
                "open_purchase_orders": open_purchase_orders,
                "near_expiry_batches": near_expiry_batches,
                "expired_batches": expired_batches,
            },
            "payment_breakdown": payment_breakdown,
            "warehouse_breakdown": warehouse_breakdown,
            "recent_sales": [_serialize_sale_row(sale) for sale in sales_qs[:20]],
        })


class DayDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_for_date(target_date)
        metrics = _sales_metrics(sales_qs)

        sale_items_qs = (
            SaleItem.objects.filter(sale__in=sales_qs)
            .values("product_id", "product__name", "product__sku")
            .annotate(
                quantity=Sum("quantity"),
                subtotal=Sum("line_subtotal"),
                tax=Sum("tax_amount"),
                total=Sum("line_total"),
            )
            .order_by("-quantity", "-total")
        )

        products = [_serialize_product_summary(row) for row in sale_items_qs]

        hourly_breakdown = []
        for hour in range(24):
            start_dt = datetime.combine(target_date, time(hour=hour))
            end_dt = start_dt + timedelta(hours=1)

            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt)
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt)

            hour_sales = sales_qs.filter(created_at__gte=start_dt, created_at__lt=end_dt)
            hourly_breakdown.append({
                "hour": f"{hour:02d}:00",
                "sales_count": hour_sales.count(),
                "total_amount": _money(hour_sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")),
            })

        sales_rows = [_serialize_sale_row(sale) for sale in sales_qs[:100]]

        anomalies = []
        cases = []
        shifts = []

        return Response({
            "date": str(target_date),

            "summary": {
                "sales_count": metrics["sales_count"],
                "transactions": metrics["transactions"],
                "items_sold": metrics["items_sold"],
                "subtotal_amount": _money(metrics["subtotal_amount"]),
                "tax_amount": _money(metrics["tax_amount"]),
                "total_amount": _money(metrics["total_amount"]),
                "total_sales": _money(metrics["total_sales"]),
                "total_cost": _money(metrics["total_cost"]),
                "total_profit": _money(metrics["total_profit"]),
            },

            # direct counters many pages use
            "sales_count": metrics["sales_count"],
            "sales": sales_rows,
            "anomalies": anomalies,
            "cases": cases,
            "shifts": shifts,

            "products": products,
            "hourly_breakdown": hourly_breakdown,
            "recent_sales": sales_rows,
        })


class HistoricalTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        days = int(request.GET.get("days") or 30)

        rows = []
        for offset in range(days - 1, -1, -1):
            current_date = target_date - timedelta(days=offset)
            sales_qs = _sales_for_date(current_date)
            metrics = _sales_metrics(sales_qs)

            rows.append({
                "date": str(current_date),
                "sales_count": metrics["sales_count"],
                "transactions": metrics["transactions"],
                "items_sold": metrics["items_sold"],
                "subtotal_amount": _money(metrics["subtotal_amount"]),
                "tax_amount": _money(metrics["tax_amount"]),
                "total_amount": _money(metrics["total_amount"]),
                "total_sales": _money(metrics["total_sales"]),
                "total_cost": _money(metrics["total_cost"]),
                "total_profit": _money(metrics["total_profit"]),
            })

        return Response({
            "date": str(target_date),
            "days": days,
            "rows": rows,
            "historical_trends": rows,
            "results": rows,
        })