from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Sum, F, DecimalField, Count
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.utils import create_audit_log
from apps.inventory.models import Product, Stock, StockBatch, Warehouse
from .models import Sale, SaleItem, SaleItemBatchAllocation


def money(value):
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def get_tax_rate_percent(product):
    tax_rate = getattr(product, "tax_rate", None)

    if not tax_rate or not getattr(tax_rate, "is_active", False):
        return Decimal("0.00")

    if getattr(tax_rate, "category", "") in ["zero_rated", "exempt"]:
        return Decimal("0.00")

    return Decimal(str(getattr(tax_rate, "rate_percent", 0) or 0))


def batch_sort_key(batch):
    expiry = batch.expiry_date

    if expiry is None:
        return (1, timezone.localdate() + timedelta(days=36500), batch.created_at)

    return (0, expiry, batch.created_at)


def serialize_batch_allocation(allocation):
    batch = allocation.stock_batch

    return {
        "id": allocation.id,
        "stock_batch_id": allocation.stock_batch_id,
        "batch_number": batch.batch_number if batch else "",
        "expiry_date": batch.expiry_date if batch else None,
        "quantity_allocated": allocation.quantity_allocated,
    }


def serialize_sale_item(item):
    line_profit = Decimal(item.line_subtotal or 0) - (
        Decimal(item.unit_cost or 0) * Decimal(item.quantity or 0)
    )

    return {
        "id": item.id,
        "product": item.product_id,
        "product_name": item.product.name if item.product else "",
        "product_sku": item.product.sku if item.product else "",
        "quantity": item.quantity,
        "unit_price": money(item.unit_price),
        "unit_cost": money(item.unit_cost),
        "tax_rate_percent": money(item.tax_rate_percent),
        "tax_amount": money(item.tax_amount),
        "line_subtotal": money(item.line_subtotal),
        "line_total": money(item.line_total),
        "line_profit": money(line_profit),
        "batch_allocations": [
            serialize_batch_allocation(allocation)
            for allocation in item.batch_allocations.select_related("stock_batch").all()
        ],
    }


def serialize_sale(sale):
    sale_items = sale.items.select_related("product").prefetch_related(
        "batch_allocations__stock_batch"
    )

    total_profit = Decimal("0.00")
    items = []

    for item in sale_items:
        line_profit = Decimal(item.line_subtotal or 0) - (
            Decimal(item.unit_cost or 0) * Decimal(item.quantity or 0)
        )
        total_profit += line_profit
        items.append(serialize_sale_item(item))

    return {
        "id": sale.id,
        "receipt_number": sale.receipt_number,
        "warehouse": sale.warehouse_id,
        "warehouse_name": sale.warehouse.name if sale.warehouse else "",
        "cashier": sale.cashier_id,
        "cashier_username": sale.cashier.username if sale.cashier else "",
        "shift": sale.shift,
        "shift_id": sale.shift,
        "payment_method": sale.payment_method,
        "subtotal_amount": money(sale.subtotal_amount),
        "tax_amount": money(sale.tax_amount),
        "total_amount": money(sale.total_amount),
        "total_profit": money(total_profit),
        "terminal_id": sale.terminal_id,
        "terminal_name": sale.terminal_name,
        "created_at": sale.created_at,
        "items": items,
    }


class SaleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Sale.objects
            .select_related("warehouse", "cashier")
            .prefetch_related("items__product", "items__batch_allocations__stock_batch")
            .all()
            .order_by("-created_at")
        )

        warehouse_id = (request.GET.get("warehouse") or "").strip()
        payment_method = (request.GET.get("payment_method") or "").strip()
        search = (request.GET.get("search") or "").strip()

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        if search:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search)
                | Q(items__product__name__icontains=search)
                | Q(items__product__sku__icontains=search)
            ).distinct()

        return Response([serialize_sale(sale) for sale in queryset])


class SaleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sale_id):
        sale = (
            Sale.objects
            .select_related("warehouse", "cashier")
            .prefetch_related("items__product", "items__batch_allocations__stock_batch")
            .filter(id=sale_id)
            .first()
        )

        if not sale:
            return Response({"detail": "Sale not found."}, status=404)

        return Response(serialize_sale(sale))


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        warehouse_id = (
            request.data.get("warehouse")
            or request.data.get("warehouse_id")
            or request.data.get("store")
        )

        payment_method = request.data.get("payment_method") or Sale.PAYMENT_CASH
        terminal = request.data.get("terminal") or {}
        items = request.data.get("items") or request.data.get("cart") or []

        if not warehouse_id:
            return Response({"detail": "Warehouse is required."}, status=400)

        if not isinstance(items, list) or not items:
            return Response({"detail": "At least one sale item is required."}, status=400)

        warehouse = Warehouse.objects.filter(id=warehouse_id, is_active=True).first()

        if not warehouse:
            return Response({"detail": "Warehouse not found."}, status=404)

        shift_value = request.data.get("shift") or request.data.get("shift_id")

        if not shift_value and request.user and request.user.is_authenticated:
            active_shift = cache.get(f"active_shift_user_{request.user.id}")
            if active_shift:
                shift_value = active_shift.get("shift_id")

        receipt_number = f"RCPT-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"

        sale = Sale.objects.create(
            receipt_number=receipt_number,
            warehouse=warehouse,
            cashier=request.user if request.user.is_authenticated else None,
            shift=shift_value if shift_value else None,
            payment_method=payment_method,
            terminal_id=str(terminal.get("terminal_id") or request.data.get("terminal_id") or ""),
            terminal_name=str(terminal.get("terminal_name") or request.data.get("terminal_name") or ""),
        )

        subtotal_amount = Decimal("0.00")
        tax_amount = Decimal("0.00")
        total_amount = Decimal("0.00")

        for row in items:
            product_id = row.get("product") or row.get("product_id") or row.get("id")
            quantity = int(row.get("quantity") or row.get("qty") or 0)

            if not product_id or quantity <= 0:
                continue

            product = Product.objects.select_related("tax_rate").filter(
                id=product_id,
                is_active=True,
            ).first()

            if not product:
                transaction.set_rollback(True)
                return Response(
                    {"detail": f"Product not found for id {product_id}."},
                    status=404,
                )

            stock = Stock.objects.select_for_update().filter(
                product=product,
                warehouse=warehouse,
            ).first()

            if not stock or int(stock.quantity or 0) < quantity:
                transaction.set_rollback(True)
                return Response(
                    {"detail": f"Insufficient stock for {product.name} in {warehouse.name}."},
                    status=400,
                )

            unit_price = Decimal(
                str(row.get("unit_price") or row.get("price") or product.selling_price or 0)
            )
            unit_cost = Decimal(str(getattr(product, "cost_price", 0) or 0))
            tax_rate_percent = get_tax_rate_percent(product)

            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=unit_cost,
                tax_rate_percent=tax_rate_percent,
            )

            available_batches = list(
                StockBatch.objects
                .select_for_update()
                .filter(
                    product=product,
                    warehouse=warehouse,
                    quantity_available__gt=0,
                )
                .exclude(status=StockBatch.STATUS_EXPIRED)
                .exclude(status=StockBatch.STATUS_QUARANTINED)
                .exclude(status=StockBatch.STATUS_WRITTEN_OFF)
            )

            available_batches.sort(key=batch_sort_key)

            remaining = quantity
            total_batch_available = sum(
                int(batch.quantity_available or 0)
                for batch in available_batches
            )

            if total_batch_available >= quantity:
                for batch in available_batches:
                    if remaining <= 0:
                        break

                    allocated_qty = min(int(batch.quantity_available or 0), remaining)

                    if allocated_qty <= 0:
                        continue

                    SaleItemBatchAllocation.objects.create(
                        sale_item=sale_item,
                        stock_batch=batch,
                        quantity_allocated=allocated_qty,
                    )

                    batch.quantity_available = int(batch.quantity_available or 0) - allocated_qty
                    batch.save(update_fields=["quantity_available"])

                    remaining -= allocated_qty

            elif total_batch_available == 0:
                pass

            else:
                transaction.set_rollback(True)
                return Response(
                    {
                        "detail": (
                            f"Insufficient batch stock for {product.name}. "
                            f"Available batch quantity: {total_batch_available}, requested: {quantity}."
                        )
                    },
                    status=400,
                )

            stock.quantity = int(stock.quantity or 0) - quantity

            try:
                stock.save(update_fields=["quantity", "updated_at"])
            except Exception:
                stock.save(update_fields=["quantity"])

            subtotal_amount += Decimal(sale_item.line_subtotal or 0)
            tax_amount += Decimal(sale_item.tax_amount or 0)
            total_amount += Decimal(sale_item.line_total or 0)

        if not sale.items.exists():
            sale.delete()
            return Response({"detail": "No valid sale items were supplied."}, status=400)

        sale.subtotal_amount = subtotal_amount
        sale.tax_amount = tax_amount
        sale.total_amount = total_amount
        sale.save(update_fields=["subtotal_amount", "tax_amount", "total_amount"])

        create_audit_log(
            actor=request.user,
            action="sale_created",
            target_type="sale",
            target_id=sale.id,
            description=f"Completed sale {sale.receipt_number}.",
            metadata={
                "sale_id": sale.id,
                "receipt_number": sale.receipt_number,
                "warehouse_id": sale.warehouse_id,
                "warehouse_name": sale.warehouse.name if sale.warehouse else "",
                "payment_method": sale.payment_method,
                "total_amount": money(sale.total_amount),
                "shift": shift_value,
                "terminal_id": sale.terminal_id,
                "terminal_name": sale.terminal_name,
                "source": "sales_api",
            },
        )

        sale = (
            Sale.objects
            .select_related("warehouse", "cashier")
            .prefetch_related("items__product", "items__batch_allocations__stock_batch")
            .get(id=sale.id)
        )

        return Response(
            {
                "detail": "Sale completed successfully.",
                "id": sale.id,
                "receipt_number": sale.receipt_number,
                "created_at": sale.created_at,
                "shift": sale.shift,
                "shift_id": sale.shift,
                "subtotal_amount": money(sale.subtotal_amount),
                "tax_amount": money(sale.tax_amount),
                "total_amount": money(sale.total_amount),
                "sale": serialize_sale(sale),
            },
            status=status.HTTP_201_CREATED,
        )


class SalesAnalyticsDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_value = (request.GET.get("range") or "today").strip().lower()
        warehouse_filter = request.GET.get("warehouse")
        today = timezone.localdate()

        if range_value == "today":
            start_date = today
            end_date = today
        elif range_value in ["7d", "week"]:
            start_date = today - timedelta(days=6)
            end_date = today
        elif range_value in ["30d", "month"]:
            start_date = today - timedelta(days=29)
            end_date = today
        else:
            start_date = today
            end_date = today

        start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        sales_qs = (
            Sale.objects
            .select_related("warehouse", "cashier")
            .filter(created_at__range=(start_dt, end_dt))
        )

        if warehouse_filter:
            sales_qs = sales_qs.filter(warehouse_id=warehouse_filter)

        subtotal_amount = sales_qs.aggregate(total=Sum("subtotal_amount"))["total"] or Decimal("0.00")
        tax_amount = sales_qs.aggregate(total=Sum("tax_amount"))["total"] or Decimal("0.00")
        total_amount = sales_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

        sale_items = SaleItem.objects.filter(sale__in=sales_qs)

        total_quantity = sale_items.aggregate(total=Sum("quantity"))["total"] or 0

        total_cost = sale_items.aggregate(
            total=Sum(
                F("unit_cost") * F("quantity"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )["total"] or Decimal("0.00")

        top_products_qs = (
            sale_items
            .values("product_id", "product__name", "product__sku")
            .annotate(
                quantity=Sum("quantity"),
                revenue=Sum("line_total"),
            )
            .order_by("-quantity", "-revenue")[:10]
        )

        top_products = [
            {
                "product_id": row["product_id"],
                "product_name": row["product__name"] or "",
                "product": row["product__name"] or "",
                "product_sku": row["product__sku"] or "",
                "sku": row["product__sku"] or "",
                "quantity": row["quantity"] or 0,
                "qty_sold": row["quantity"] or 0,
                "units_sold": row["quantity"] or 0,
                "revenue": money(row["revenue"] or Decimal("0.00")),
                "total_revenue": money(row["revenue"] or Decimal("0.00")),
                "profit": money(Decimal("0.00")),
            }
            for row in top_products_qs
        ]

        payment_breakdown_qs = (
            sales_qs
            .values("payment_method")
            .annotate(
                sales_count=Count("id"),
                total=Sum("total_amount"),
            )
            .order_by("payment_method")
        )

        payment_breakdown = [
            {
                "payment_method": row["payment_method"],
                "sales_count": row["sales_count"] or 0,
                "transactions": row["sales_count"] or 0,
                "total_amount": money(row["total"] or Decimal("0.00")),
                "sales": money(row["total"] or Decimal("0.00")),
            }
            for row in payment_breakdown_qs
        ]

        warehouse_breakdown_qs = (
            sales_qs
            .values("warehouse_id", "warehouse__name")
            .annotate(
                sales_count=Count("id"),
                total=Sum("total_amount"),
            )
            .order_by("-total")
        )

        warehouse_breakdown = [
            {
                "warehouse_id": row["warehouse_id"],
                "warehouse": row["warehouse__name"] or "",
                "warehouse_name": row["warehouse__name"] or "",
                "sales_count": row["sales_count"] or 0,
                "transactions": row["sales_count"] or 0,
                "sales": money(row["total"] or Decimal("0.00")),
                "sales_value": money(row["total"] or Decimal("0.00")),
                "sales_total": money(row["total"] or Decimal("0.00")),
                "total_sales": money(row["total"] or Decimal("0.00")),
                "total_amount": money(row["total"] or Decimal("0.00")),
                "revenue": money(row["total"] or Decimal("0.00")),
                "profit": money(Decimal("0.00")),
                "profit_total": money(Decimal("0.00")),
            }
            for row in warehouse_breakdown_qs
        ]

        average_sale = (
            total_amount / sales_qs.count()
            if sales_qs.count()
            else Decimal("0.00")
        )

        recent_sales = [
            serialize_sale(sale)
            for sale in sales_qs.order_by("-created_at")[:20]
        ]

        return Response({
            "range": range_value,
            "date_from": str(start_date),
            "date_to": str(end_date),
            "summary": {
                "sales_count": sales_qs.count(),
                "transactions": sales_qs.count(),
                "transaction_count": sales_qs.count(),
                "total_quantity": total_quantity,
                "items_sold": total_quantity,
                "subtotal_amount": money(subtotal_amount),
                "tax_amount": money(tax_amount),
                "total_amount": money(total_amount),
                "total_sales": money(total_amount),
                "total_cost": money(total_cost),
                "total_profit": money(total_amount - total_cost),
                "average_sale": money(average_sale),
            },
            "top_products": top_products,
            "payment_breakdown": payment_breakdown,
            "warehouse_breakdown": warehouse_breakdown,
            "recent_sales": recent_sales,
        })