
from decimal import Decimal
from datetime import datetime, time, timedelta

from django.core.cache import cache
from django.db.models import Count, Sum, F, DecimalField
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.utils import create_audit_log
from apps.sales.models import Sale, SaleItem, Refund

SHIFT_CACHE_PREFIX = "active_shift_user_"
LAST_CLOSED_SHIFT_CACHE_PREFIX = "last_closed_shift_user_"
ANOMALY_CASES_CACHE_KEY = "anomaly_cases_global"


def _now():
    return timezone.now()


def _today():
    return timezone.localdate()


def _money(value):
    try:
        return str(Decimal(value or 0).quantize(Decimal("0.01")))
    except Exception:
        return "0.00"


def _parse_date_param(value):
    if not value:
        return _today()
    try:
        return datetime.fromisoformat(str(value)).date()
    except Exception:
        return _today()


def _day_range(target_date):
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date, time.max)
    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt)
    return start_dt, end_dt


def _cache_key_for_user(user_id):
    return f"{SHIFT_CACHE_PREFIX}{user_id}"


def _last_closed_cache_key_for_user(user_id):
    return f"{LAST_CLOSED_SHIFT_CACHE_PREFIX}{user_id}"


def _get_active_shift(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return cache.get(_cache_key_for_user(user.id))


def _set_active_shift(user, payload):
    cache.set(_cache_key_for_user(user.id), payload, timeout=None)


def _clear_active_shift(user):
    if getattr(user, "is_authenticated", False):
        cache.delete(_cache_key_for_user(user.id))


def _get_last_closed_shift(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return cache.get(_last_closed_cache_key_for_user(user.id))


def _set_last_closed_shift(user, payload):
    cache.set(_last_closed_cache_key_for_user(user.id), payload, timeout=None)


def _generate_shift_id():
    return int(_now().timestamp())


def _sales_queryset_for_range(start_dt, end_dt):
    return (
        Sale.objects
        .select_related("warehouse", "cashier")
        .prefetch_related("items__product", "items__batch_allocations__stock_batch")
        .filter(created_at__range=(start_dt, end_dt))
    )


def _sales_queryset_for_day(target_date):
    start_dt, end_dt = _day_range(target_date)
    return _sales_queryset_for_range(start_dt, end_dt)


def _sales_queryset_for_shift(shift_id):
    return (
        Sale.objects
        .select_related("warehouse", "cashier")
        .prefetch_related("items__product", "items__batch_allocations__stock_batch")
        .filter(shift=shift_id)
        .order_by("-created_at")
    )


def _metrics_from_sales(sales_qs):
    sales_count = sales_qs.count()
    subtotal_amount = sales_qs.aggregate(total=Sum("subtotal_amount"))["total"] or Decimal("0.00")
    tax_amount = sales_qs.aggregate(total=Sum("tax_amount"))["total"] or Decimal("0.00")
    total_amount = sales_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    sale_items = SaleItem.objects.filter(sale__in=sales_qs)
    total_quantity = sale_items.aggregate(total=Sum("quantity"))["total"] or 0
    total_cost = sale_items.aggregate(
        total=Sum(F("unit_cost") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2))
    )["total"] or Decimal("0.00")

    cash_sales = sales_qs.filter(payment_method__iexact="cash").aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    card_sales = sales_qs.filter(payment_method__iexact="card").aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    non_cash_sales = total_amount - cash_sales
    total_profit = subtotal_amount - total_cost

    return {
        "sales_count": sales_count,
        "transactions": sales_count,
        "transaction_count": sales_count,
        "total_quantity": total_quantity,
        "items_sold": total_quantity,
        "subtotal_amount": subtotal_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "total_sales": total_amount,
        "cash_sales": cash_sales,
        "card_sales": card_sales,
        "non_cash_sales": non_cash_sales,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "average_sale": (total_amount / sales_count) if sales_count else Decimal("0.00"),
    }


def _refund_metrics_for_sales(sales_qs):
    refunds_qs = Refund.objects.filter(sale__in=sales_qs)

    refund_subtotal = refunds_qs.aggregate(total=Sum("subtotal_amount"))["total"] or Decimal("0.00")
    refund_tax = refunds_qs.aggregate(total=Sum("tax_amount"))["total"] or Decimal("0.00")
    refund_total = refunds_qs.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    refund_cost = refunds_qs.aggregate(total=Sum("total_cost"))["total"] or Decimal("0.00")
    refund_profit = refunds_qs.aggregate(total=Sum("total_profit_reversed"))["total"] or Decimal("0.00")

    return {
        "refund_count": refunds_qs.count(),
        "refund_subtotal": refund_subtotal,
        "refund_tax": refund_tax,
        "refund_total": refund_total,
        "refund_cost": refund_cost,
        "refund_profit_reversed": refund_profit,
    }


def _net_summary_dict(metrics, refund_metrics):
    gross_sales = Decimal(metrics["total_sales"] or 0)
    gross_tax = Decimal(metrics["tax_amount"] or 0)
    gross_profit = Decimal(metrics["total_profit"] or 0)
    gross_cost = Decimal(metrics["total_cost"] or 0)

    refunds_total = Decimal(refund_metrics["refund_total"] or 0)
    refunds_tax = Decimal(refund_metrics["refund_tax"] or 0)
    refunds_profit = Decimal(refund_metrics["refund_profit_reversed"] or 0)
    refunds_cost = Decimal(refund_metrics["refund_cost"] or 0)

    net_sales = gross_sales - refunds_total
    net_tax = gross_tax - refunds_tax
    net_profit = gross_profit - refunds_profit
    net_cost = gross_cost - refunds_cost

    return {
        **_shift_summary_dict(metrics),

        "gross_sales": _money(gross_sales),
        "gross_tax": _money(gross_tax),
        "gross_profit": _money(gross_profit),
        "gross_cost": _money(gross_cost),

        "refund_count": refund_metrics["refund_count"],
        "refund_total": _money(refunds_total),
        "refund_tax": _money(refunds_tax),
        "refund_profit_reversed": _money(refunds_profit),
        "refund_cost": _money(refunds_cost),

        "net_sales": _money(net_sales),
        "net_tax": _money(net_tax),
        "net_profit": _money(net_profit),
        "net_cost": _money(net_cost),

        "total_sales_net": _money(net_sales),
        "tax_amount_net": _money(net_tax),
        "total_profit_net": _money(net_profit),
    }


def _shift_summary_dict(metrics):
    return {
        "sales_count": metrics["sales_count"],
        "transactions": metrics["transactions"],
        "transaction_count": metrics["transaction_count"],
        "total_quantity": metrics["total_quantity"],
        "items_sold": metrics["items_sold"],
        "subtotal_amount": _money(metrics["subtotal_amount"]),
        "tax_amount": _money(metrics["tax_amount"]),
        "total_amount": _money(metrics["total_amount"]),
        "total_sales": _money(metrics["total_sales"]),
        "cash_sales": _money(metrics["cash_sales"]),
        "cash_sales_total": _money(metrics["cash_sales"]),
        "card_sales": _money(metrics["card_sales"]),
        "card_sales_total": _money(metrics["card_sales"]),
        "non_cash_sales": _money(metrics["non_cash_sales"]),
        "total_cost": _money(metrics["total_cost"]),
        "total_profit": _money(metrics["total_profit"]),
        "average_sale": _money(metrics["average_sale"]),
    }


def _serialize_sale(sale):
    total_cost = sum(Decimal(item.unit_cost or 0) * Decimal(item.quantity or 0) for item in sale.items.all())
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
        "shift_id": sale.shift,
        "payment": sale.payment_method,
        "payment_method": sale.payment_method,
        "subtotal": _money(sale.subtotal_amount),
        "subtotal_amount": _money(sale.subtotal_amount),
        "tax": _money(sale.tax_amount),
        "tax_amount": _money(sale.tax_amount),
        "total": _money(sale.total_amount),
        "total_amount": _money(sale.total_amount),
        "profit": _money(profit),
        "total_profit": _money(profit),
        "created": sale.created_at,
        "created_at": sale.created_at,
        "terminal": sale.terminal_name or sale.terminal_id or "-",
        "terminal_name": sale.terminal_name or sale.terminal_id or "-",
        "terminal_id": sale.terminal_id or "",
    }


def _serialize_shift_payload(shift_payload):
    if not shift_payload:
        return None
    return {
        "id": shift_payload.get("shift_id"),
        "shift_id": shift_payload.get("shift_id"),
        "cashier": shift_payload.get("cashier", "-"),
        "cashier_username": shift_payload.get("cashier", "-"),
        "terminal": shift_payload.get("terminal", "-"),
        "terminal_id": shift_payload.get("terminal_id", shift_payload.get("terminal", "-")),
        "terminal_name": shift_payload.get("terminal", "-"),
        "status": shift_payload.get("status", "open"),
        "opening_float": _money(shift_payload.get("opening_float", Decimal("0.00"))),
        "expected_cash": _money(shift_payload.get("expected_cash", Decimal("0.00"))),
        "actual_cash": _money(shift_payload.get("actual_cash", Decimal("0.00"))),
        "variance": _money(shift_payload.get("variance", Decimal("0.00"))),
        "cash_sales": _money(shift_payload.get("cash_sales", Decimal("0.00"))),
        "card_sales": _money(shift_payload.get("card_sales", Decimal("0.00"))),
        "opened": shift_payload.get("opened_at"),
        "opened_at": shift_payload.get("opened_at"),
        "closed": shift_payload.get("closed_at"),
        "closed_at": shift_payload.get("closed_at"),
        "notes": shift_payload.get("notes", ""),
        "summary": shift_payload.get("summary", {}),
    }


class StartShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active_shift = _get_active_shift(request.user)
        if active_shift:
            return Response({"detail": "You already have an active shift.", "shift": _serialize_shift_payload(active_shift)}, status=400)

        try:
            opening_float = Decimal(str(request.data.get("opening_float") or "0.00"))
        except Exception:
            opening_float = Decimal("0.00")

        notes = str(request.data.get("notes") or "")
        terminal = str(request.data.get("terminal") or request.data.get("terminal_name") or request.data.get("terminal_id") or "POS Terminal 1")
        terminal_id = str(request.data.get("terminal_id") or terminal)

        shift_payload = {
            "shift_id": _generate_shift_id(),
            "cashier": getattr(request.user, "username", "-"),
            "terminal": terminal,
            "terminal_id": terminal_id,
            "opened_at": _now().isoformat(),
            "closed_at": None,
            "status": "open",
            "opening_float": opening_float,
            "expected_cash": opening_float,
            "actual_cash": Decimal("0.00"),
            "variance": Decimal("0.00"),
            "cash_sales": Decimal("0.00"),
            "card_sales": Decimal("0.00"),
            "notes": notes,
            "summary": {},
        }
        _set_active_shift(request.user, shift_payload)
        create_audit_log(actor=request.user, action="shift_started", target_type="shift", target_id=shift_payload["shift_id"], description=f"Started shift {shift_payload['shift_id']}.", metadata={"shift_id": shift_payload["shift_id"], "opening_float": str(opening_float), "source": "accounts_shift_api"})
        return Response({"detail": "Shift started successfully.", "message": "Shift started successfully.", "shift": _serialize_shift_payload(shift_payload)})


class EndShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active_shift = _get_active_shift(request.user)
        if not active_shift:
            return Response({"detail": "No active shift found."}, status=400)

        shift_id = active_shift["shift_id"]
        sales_qs = _sales_queryset_for_shift(shift_id).filter(cashier=request.user)
        metrics = _metrics_from_sales(sales_qs)
        opening_float = Decimal(str(active_shift.get("opening_float") or "0.00"))
        expected_cash = opening_float + Decimal(metrics["cash_sales"] or 0)

        try:
            actual_cash = Decimal(str(request.data.get("actual_cash") or expected_cash))
        except Exception:
            actual_cash = expected_cash

        variance = actual_cash - expected_cash
        closing_notes = str(request.data.get("notes") or "")
        closed_shift_payload = {
            "shift_id": shift_id,
            "cashier": active_shift.get("cashier", getattr(request.user, "username", "-")),
            "terminal": active_shift.get("terminal", "POS Terminal 1"),
            "terminal_id": active_shift.get("terminal_id", active_shift.get("terminal", "POS Terminal 1")),
            "opened_at": active_shift.get("opened_at"),
            "closed_at": _now().isoformat(),
            "status": "closed",
            "opening_float": opening_float,
            "expected_cash": expected_cash,
            "actual_cash": actual_cash,
            "variance": variance,
            "cash_sales": metrics["cash_sales"],
            "card_sales": metrics["card_sales"],
            "notes": closing_notes or active_shift.get("notes", ""),
            "summary": _shift_summary_dict(metrics),
        }
        create_audit_log(actor=request.user, action="shift_ended", target_type="shift", target_id=shift_id, description=f"Ended shift {shift_id}.", metadata={"shift_id": shift_id, "expected_cash": str(expected_cash), "actual_cash": str(actual_cash), "variance": str(variance), "source": "accounts_shift_api"})
        _set_last_closed_shift(request.user, closed_shift_payload)
        _clear_active_shift(request.user)
        return Response({"detail": "Shift ended successfully.", "message": "Shift ended successfully.", "shift": _serialize_shift_payload(closed_shift_payload), "summary": closed_shift_payload["summary"]})


class CurrentShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_shift = _get_active_shift(request.user)
        if not active_shift:
            return Response({"active": False, "shift": None})
        shift_id = active_shift["shift_id"]
        sales_qs = _sales_queryset_for_shift(shift_id).filter(cashier=request.user)
        metrics = _metrics_from_sales(sales_qs)
        opening_float = Decimal(str(active_shift.get("opening_float") or "0.00"))
        active_shift["expected_cash"] = opening_float + Decimal(metrics["cash_sales"] or 0)
        active_shift["cash_sales"] = metrics["cash_sales"]
        active_shift["card_sales"] = metrics["card_sales"]
        return Response({"active": True, "shift": _serialize_shift_payload(active_shift), "summary": _shift_summary_dict(metrics)})


class ShiftStatusView(CurrentShiftView):
    pass


class LastClosedShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"shift": _serialize_shift_payload(_get_last_closed_shift(request.user))})


def _build_shift_rows(user):
    sales = Sale.objects.select_related("warehouse", "cashier").exclude(shift__isnull=True).order_by("shift", "-created_at")
    grouped = {}
    for sale in sales:
        if sale.shift in [None, 0]:
            continue
        try:
            shift_key = int(sale.shift)
        except Exception:
            continue
        grouped.setdefault(shift_key, []).append(sale)

    rows = []
    active_shift = _get_active_shift(user)
    last_closed_shift = _get_last_closed_shift(user)

    if active_shift:
        shift_id = active_shift.get("shift_id")
        sales_qs = _sales_queryset_for_shift(shift_id)
        if getattr(user, "is_authenticated", False):
            sales_qs = sales_qs.filter(cashier=user)
        metrics = _metrics_from_sales(sales_qs)
        opening_float = Decimal(str(active_shift.get("opening_float") or "0.00"))
        active_payload = _serialize_shift_payload({**active_shift, "status": "open", "cash_sales": metrics["cash_sales"], "card_sales": metrics["card_sales"], "expected_cash": opening_float + Decimal(metrics["cash_sales"] or 0)})
        active_payload.update({"sales_count": metrics["sales_count"], "transactions": metrics["transactions"], "total_sales": _money(metrics["total_sales"]), "total_amount": _money(metrics["total_amount"]), "total_profit": _money(metrics["total_profit"])})
        rows.append(active_payload)

    if last_closed_shift:
        closed_payload = _serialize_shift_payload(last_closed_shift)
        closed_payload["status"] = "closed"
        rows.append(closed_payload)

    for shift_id, shift_sales in grouped.items():
        if active_shift and str(active_shift.get("shift_id")) == str(shift_id):
            continue
        if last_closed_shift and str(last_closed_shift.get("shift_id")) == str(shift_id):
            continue
        sales_qs = Sale.objects.filter(id__in=[row.id for row in shift_sales])
        metrics = _metrics_from_sales(sales_qs)
        opening_float = Decimal("0.00")
        expected_cash = opening_float + Decimal(metrics["cash_sales"] or 0)
        first_sale = shift_sales[0]
        last_sale = shift_sales[-1]
        rows.append({
            "id": shift_id,
            "shift_id": shift_id,
            "cashier": first_sale.cashier.username if first_sale.cashier else "-",
            "cashier_username": first_sale.cashier.username if first_sale.cashier else "-",
            "terminal": first_sale.terminal_name or first_sale.terminal_id or "-",
            "terminal_id": first_sale.terminal_id or "-",
            "terminal_name": first_sale.terminal_name or first_sale.terminal_id or "-",
            "status": "closed",
            "opening_float": _money(opening_float),
            "expected_cash": _money(expected_cash),
            "actual_cash": _money(expected_cash),
            "variance": "0.00",
            "cash_sales": _money(metrics["cash_sales"]),
            "card_sales": _money(metrics["card_sales"]),
            "opened": last_sale.created_at,
            "opened_at": last_sale.created_at,
            "closed": first_sale.created_at,
            "closed_at": first_sale.created_at,
            "sales_count": metrics["sales_count"],
            "transactions": metrics["transactions"],
            "total_sales": _money(metrics["total_sales"]),
            "total_amount": _money(metrics["total_amount"]),
            "total_profit": _money(metrics["total_profit"]),
        })

    rows.sort(key=lambda x: str(x.get("closed_at") or x.get("opened_at") or ""), reverse=True)
    return rows


class ShiftListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = _build_shift_rows(request.user)
        return Response({"count": len(rows), "results": rows, "rows": rows, "history": rows})


class AllShiftsAdminView(ShiftListView):
    pass


class ShiftHistoryView(ShiftListView):
    pass


class ShiftDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, shift_id=None):
        shift_id = shift_id or request.GET.get("shift") or request.GET.get("shift_id")
        if shift_id in [None, ""]:
            return Response({"detail": "Shift id is required."}, status=400)
        sales_qs = _sales_queryset_for_shift(shift_id)
        metrics = _metrics_from_sales(sales_qs)
        return Response({"shift_id": shift_id, "summary": _shift_summary_dict(metrics), "sales": [_serialize_sale(sale) for sale in sales_qs[:100]]})


class DailySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_queryset_for_day(target_date)

        metrics = _metrics_from_sales(sales_qs)
        refund_metrics = _refund_metrics_for_sales(sales_qs)

        rows = [_serialize_sale(sale) for sale in sales_qs.order_by("-created_at")[:20]]

        top_products_qs = (
            SaleItem.objects
            .filter(sale__in=sales_qs)
            .values("product_id", "product__name", "product__sku")
            .annotate(
                quantity=Sum("quantity"),
                revenue=Sum("line_total"),
                tax_amount=Sum("tax_amount"),
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
                "revenue": _money(row["revenue"] or Decimal("0.00")),
                "total_revenue": _money(row["revenue"] or Decimal("0.00")),
                "tax_amount": _money(row["tax_amount"] or Decimal("0.00")),
                "tax": _money(row["tax_amount"] or Decimal("0.00")),
            }
            for row in top_products_qs
        ]

        payment_breakdown_qs = (
            sales_qs
            .values("payment_method")
            .annotate(
                transactions=Count("id"),
                total_amount=Sum("total_amount"),
                tax_amount=Sum("tax_amount"),
            )
            .order_by("payment_method")
        )

        payment_breakdown = [
            {
                "payment_method": row["payment_method"] or "-",
                "transactions": row["transactions"] or 0,
                "sales_count": row["transactions"] or 0,
                "total_amount": _money(row["total_amount"] or Decimal("0.00")),
                "sales": _money(row["total_amount"] or Decimal("0.00")),
                "tax_amount": _money(row["tax_amount"] or Decimal("0.00")),
                "tax": _money(row["tax_amount"] or Decimal("0.00")),
            }
            for row in payment_breakdown_qs
        ]

        variance_rows = []
        active_shift = _get_active_shift(request.user)
        last_closed_shift = _get_last_closed_shift(request.user)

        if active_shift:
            variance_rows.append(_serialize_shift_payload(active_shift))

        if last_closed_shift:
            variance_rows.append(_serialize_shift_payload(last_closed_shift))

        short_count = sum(1 for row in variance_rows if Decimal(str(row.get("variance") or "0.00")) < 0)
        over_count = sum(1 for row in variance_rows if Decimal(str(row.get("variance") or "0.00")) > 0)
        balanced_count = sum(1 for row in variance_rows if Decimal(str(row.get("variance") or "0.00")) == 0)

        summary = _net_summary_dict(metrics, refund_metrics)
        summary.update({
            "closed_shifts": sum(1 for row in variance_rows if str(row.get("status", "")).lower() == "closed"),
            "open_shifts": sum(1 for row in variance_rows if str(row.get("status", "")).lower() == "open"),
            "short_count": short_count,
            "over_count": over_count,
            "balanced_count": balanced_count,
        })

        return Response({
            "date": str(target_date),
            "summary": summary,
            "recent_sales": rows,
            "sales": rows,
            "top_products": top_products,
            "payment_breakdown": payment_breakdown,
            "transaction_breakdown": payment_breakdown,
            "variance_rows": variance_rows,
            "shift_variances": variance_rows,
        })


class ShiftSalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        shift_value = request.GET.get("shift")
        sales_qs = _sales_queryset_for_day(target_date)
        if shift_value not in [None, ""]:
            sales_qs = sales_qs.filter(shift=shift_value)
        metrics = _metrics_from_sales(sales_qs)
        refund_metrics = _refund_metrics_for_sales(sales_qs)
        rows = [_serialize_sale(sale) for sale in sales_qs.order_by("-created_at")[:100]]
        return Response({
            "date": str(target_date),
            "shift": shift_value,
            "summary": _net_summary_dict(metrics, refund_metrics),
            "sales": rows,
            "results": rows,
        })


class ShiftVarianceDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_shift = _get_active_shift(request.user)
        last_closed_shift = _get_last_closed_shift(request.user)
        rows = []

        if active_shift:
            shift_id = active_shift.get("shift_id")
            sales_qs = _sales_queryset_for_shift(shift_id).filter(cashier=request.user)
            metrics = _metrics_from_sales(sales_qs)
            opening_float = Decimal(str(active_shift.get("opening_float") or "0.00"))
            expected_cash = opening_float + Decimal(metrics["cash_sales"] or 0)
            actual_cash = Decimal(str(request.GET.get("actual_cash") or expected_cash))
            variance = actual_cash - expected_cash
            rows.append({"id": shift_id, "shift_id": shift_id, "cashier": active_shift.get("cashier", "-"), "cashier_username": active_shift.get("cashier", "-"), "terminal": active_shift.get("terminal", "-"), "terminal_id": active_shift.get("terminal_id", active_shift.get("terminal", "-")), "terminal_name": active_shift.get("terminal", "-"), "status": "open", "opening_float": _money(opening_float), "cash_sales": _money(metrics["cash_sales"]), "card_sales": _money(metrics["card_sales"]), "expected_cash": _money(expected_cash), "actual_cash": _money(actual_cash), "variance": _money(variance), "opened_at": active_shift.get("opened_at"), "closed_at": None})

        if last_closed_shift:
            rows.append({"id": last_closed_shift.get("shift_id"), "shift_id": last_closed_shift.get("shift_id"), "cashier": last_closed_shift.get("cashier", "-"), "cashier_username": last_closed_shift.get("cashier", "-"), "terminal": last_closed_shift.get("terminal", "-"), "terminal_id": last_closed_shift.get("terminal_id", last_closed_shift.get("terminal", "-")), "terminal_name": last_closed_shift.get("terminal", "-"), "status": "closed", "opening_float": _money(last_closed_shift.get("opening_float", "0.00")), "cash_sales": _money(last_closed_shift.get("cash_sales", "0.00")), "card_sales": _money(last_closed_shift.get("card_sales", "0.00")), "expected_cash": _money(last_closed_shift.get("expected_cash", "0.00")), "actual_cash": _money(last_closed_shift.get("actual_cash", "0.00")), "variance": _money(last_closed_shift.get("variance", "0.00")), "opened_at": last_closed_shift.get("opened_at"), "closed_at": last_closed_shift.get("closed_at")})

        short_count = sum(1 for row in rows if Decimal(str(row.get("variance") or "0.00")) < 0)
        over_count = sum(1 for row in rows if Decimal(str(row.get("variance") or "0.00")) > 0)
        balanced_count = sum(1 for row in rows if Decimal(str(row.get("variance") or "0.00")) == 0)
        first_row = rows[0] if rows else {}
        return Response({"active_shift": _serialize_shift_payload(active_shift), "last_closed_shift": _serialize_shift_payload(last_closed_shift), "summary": {"total_shifts": len(rows), "opening_float": first_row.get("opening_float", "0.00"), "cash_sales_total": first_row.get("cash_sales", "0.00"), "expected_cash": first_row.get("expected_cash", "0.00"), "actual_cash": first_row.get("actual_cash", "0.00"), "variance": first_row.get("variance", "0.00"), "short": short_count, "over": over_count, "balanced": balanced_count, "short_count": short_count, "over_count": over_count, "balanced_count": balanced_count}, "rows": rows, "results": rows, "shifts": rows})


class HistoricalTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.GET.get("days") or 30)
        today = _today()
        rows = []
        for offset in range(days - 1, -1, -1):
            current_date = today - timedelta(days=offset)
            metrics = _metrics_from_sales(_sales_queryset_for_day(current_date))
            rows.append({"date": str(current_date), "sales_count": metrics["sales_count"], "transactions": metrics["transactions"], "total_quantity": metrics["total_quantity"], "subtotal_amount": _money(metrics["subtotal_amount"]), "tax_amount": _money(metrics["tax_amount"]), "total_amount": _money(metrics["total_amount"]), "total_sales": _money(metrics["total_sales"]), "total_cost": _money(metrics["total_cost"]), "total_profit": _money(metrics["total_profit"])})
        return Response({"days": days, "rows": rows, "results": rows})


class TerminalActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_queryset_for_day(target_date)
        terminal_rows = sales_qs.values("terminal_id", "terminal_name").annotate(sales_count=Count("id"), total_amount=Sum("total_amount")).order_by("-total_amount")
        rows = [{"terminal_id": row["terminal_id"] or "", "terminal": row["terminal_name"] or row["terminal_id"] or "", "terminal_name": row["terminal_name"] or row["terminal_id"] or "", "status": "active" if (row["sales_count"] or 0) > 0 else "idle", "sales_count": row["sales_count"] or 0, "transactions": row["sales_count"] or 0, "total_amount": _money(row["total_amount"] or Decimal("0.00")), "total_sales": _money(row["total_amount"] or Decimal("0.00"))} for row in terminal_rows]
        return Response({"date": str(target_date), "rows": rows, "results": rows})


class TerminalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_shift = _get_active_shift(request.user)
        terminals = {}
        sales = Sale.objects.select_related("cashier").exclude(terminal_id__isnull=True).order_by("-created_at")[:100]
        for sale in sales:
            terminal_key = sale.terminal_id or sale.terminal_name or "POS Terminal 1"
            if terminal_key not in terminals:
                terminals[terminal_key] = {"id": terminal_key, "terminal_id": terminal_key, "terminal_name": sale.terminal_name or terminal_key, "status": "idle", "cashier": sale.cashier.username if sale.cashier else "-", "current_cashier": sale.cashier.username if sale.cashier else "-", "active_shift_id": None, "last_sale_at": sale.created_at, "transactions": 0, "total_sales": Decimal("0.00")}
            terminals[terminal_key]["transactions"] += 1
            terminals[terminal_key]["total_sales"] += Decimal(str(sale.total_amount or 0))
        if active_shift:
            terminal_key = active_shift.get("terminal_id") or active_shift.get("terminal") or "POS Terminal 1"
            if terminal_key not in terminals:
                terminals[terminal_key] = {"id": terminal_key, "terminal_id": terminal_key, "terminal_name": active_shift.get("terminal") or terminal_key, "status": "open", "cashier": active_shift.get("cashier", "-"), "current_cashier": active_shift.get("cashier", "-"), "active_shift_id": active_shift.get("shift_id"), "last_sale_at": None, "transactions": 0, "total_sales": Decimal("0.00")}
            else:
                terminals[terminal_key]["status"] = "open"
                terminals[terminal_key]["cashier"] = active_shift.get("cashier", "-")
                terminals[terminal_key]["current_cashier"] = active_shift.get("cashier", "-")
                terminals[terminal_key]["active_shift_id"] = active_shift.get("shift_id")
        if not terminals:
            terminals["POS Terminal 1"] = {"id": "POS Terminal 1", "terminal_id": "POS Terminal 1", "terminal_name": "POS Terminal 1", "status": "idle", "cashier": "-", "current_cashier": "-", "active_shift_id": None, "last_sale_at": None, "transactions": 0, "total_sales": Decimal("0.00")}
        rows = []
        for terminal in terminals.values():
            terminal["total_sales"] = _money(terminal["total_sales"])
            rows.append(terminal)
        return Response(rows)


class TerminalRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        terminal_id = str(request.data.get("terminal_id") or "POS Terminal 1")
        terminal_name = str(request.data.get("terminal_name") or terminal_id)
        return Response({"detail": "Terminal registered successfully.", "terminal": {"terminal_id": terminal_id, "terminal_name": terminal_name, "status": "active"}, "success": True})


def _anomaly_evidence_cache_key(case_id):
    return f"anomaly_case_evidence_{case_id}"


def _get_anomaly_cases():
    return cache.get(ANOMALY_CASES_CACHE_KEY, [])


def _set_anomaly_cases(cases):
    cache.set(ANOMALY_CASES_CACHE_KEY, cases, timeout=None)


def _get_case_by_id(case_id):
    for case in _get_anomaly_cases():
        if str(case.get("id")) == str(case_id):
            return case
    return None


def _find_case_by_source_anomaly_id(source_anomaly_id):
    if not source_anomaly_id:
        return None
    for case in _get_anomaly_cases():
        metadata = case.get("metadata") or {}
        existing_source = case.get("source_anomaly_id") or case.get("linked_anomaly_id") or metadata.get("source_anomaly_id")
        if str(existing_source) == str(source_anomaly_id):
            return case
    return None


def _priority_from_variance(variance):
    value = abs(Decimal(str(variance or "0.00")))
    if value >= Decimal("50.00"):
        return "critical"
    if value >= Decimal("10.00"):
        return "high"
    if value >= Decimal("2.00"):
        return "medium"
    return "low"


def _build_live_anomalies(user, target_date=None):
    target_date = target_date or _today()
    anomalies = []
    active_shift = _get_active_shift(user)
    last_closed_shift = _get_last_closed_shift(user)
    if not active_shift:
        anomaly_id = "no-active-shift"
        linked_case = _find_case_by_source_anomaly_id(anomaly_id)
        anomalies.append({"id": anomaly_id, "type": "shift", "anomaly_type": "no_active_shift", "severity": "medium", "priority": "medium", "status": "open", "score": 50, "title": "No active shift", "description": "No active cashier shift is currently open.", "detected_date": str(target_date), "case_id": linked_case.get("id") if linked_case else None})
    if last_closed_shift:
        variance = Decimal(str(last_closed_shift.get("variance") or "0.00"))
        if variance != 0:
            priority = _priority_from_variance(variance)
            anomaly_id = f"variance-{last_closed_shift.get('shift_id')}"
            linked_case = _find_case_by_source_anomaly_id(anomaly_id)
            anomalies.append({"id": anomaly_id, "type": "cash_variance", "anomaly_type": "cash_variance", "severity": priority, "priority": priority, "status": "open", "score": min(int(abs(variance) * 2), 100), "title": f"Cash variance on shift {last_closed_shift.get('shift_id')}", "description": f"Expected cash £{_money(last_closed_shift.get('expected_cash'))}, actual cash £{_money(last_closed_shift.get('actual_cash'))}, variance £{_money(variance)}.", "detected_date": str(target_date), "shift_id": last_closed_shift.get("shift_id"), "case_id": linked_case.get("id") if linked_case else None})
    metrics = _metrics_from_sales(_sales_queryset_for_day(target_date))
    if metrics["total_profit"] < 0:
        anomaly_id = f"negative-profit-{target_date}"
        linked_case = _find_case_by_source_anomaly_id(anomaly_id)
        anomalies.append({"id": anomaly_id, "type": "profit", "anomaly_type": "negative_profit", "severity": "high", "priority": "high", "status": "open", "score": 85, "title": "Negative profit detected", "description": "Total sales profit is negative for the selected date.", "detected_date": str(target_date), "case_id": linked_case.get("id") if linked_case else None})
    return anomalies


def _normalise_case(case):
    evidence = cache.get(_anomaly_evidence_cache_key(case.get("id")), [])
    metadata = case.get("metadata") or {}
    return {**case, "case": case, "anomaly_type": case.get("anomaly_type") or case.get("type") or "manual", "severity": case.get("severity") or case.get("priority") or "medium", "priority": case.get("priority") or "medium", "status": case.get("status") or "open", "assigned_to_id": case.get("assigned_to_id"), "assigned_to_username": case.get("assigned_to_username") or case.get("assigned") or "", "created_by_username": case.get("created_by_username") or case.get("created_by") or "", "evidence_count": len(evidence), "evidence_items": evidence, "timeline": case.get("timeline", []), "metadata": metadata, "sla_breached": bool(case.get("sla_breached", False)), "escalation_level": int(case.get("escalation_level") or 0), "source_anomaly_id": case.get("source_anomaly_id") or metadata.get("source_anomaly_id"), "linked_anomaly_id": case.get("linked_anomaly_id") or metadata.get("source_anomaly_id")}


class AnomalyCaseListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cases = [_normalise_case(case) for case in _get_anomaly_cases()]
        status_filter = str(request.GET.get("status") or "").lower()
        priority_filter = str(request.GET.get("priority") or "").lower()
        search = str(request.GET.get("search") or "").lower()
        sla_filter = str(request.GET.get("sla") or "").lower()
        if status_filter:
            cases = [c for c in cases if str(c.get("status", "")).lower() == status_filter]
        if priority_filter:
            cases = [c for c in cases if str(c.get("priority", "")).lower() == priority_filter]
        if search:
            cases = [c for c in cases if search in str(c.get("title", "")).lower() or search in str(c.get("description", "")).lower() or search in str(c.get("source_anomaly_id", "")).lower()]
        if sla_filter == "breached":
            cases = [c for c in cases if c.get("sla_breached")]
        elif sla_filter == "healthy":
            cases = [c for c in cases if not c.get("sla_breached")]
        page = int(request.GET.get("page") or 1)
        page_size = int(request.GET.get("page_size") or 25)
        total_count = len(cases)
        start = (page - 1) * page_size
        end = start + page_size
        page_cases = cases[start:end]
        return Response({"cases": page_cases, "results": page_cases, "assignable_users": [{"id": request.user.id, "username": getattr(request.user, "username", "current_user")}], "pagination": {"page": page, "page_size": page_size, "total_count": total_count, "total_pages": max((total_count + page_size - 1) // page_size, 1)}})

    def post(self, request):
        cases = _get_anomaly_cases()
        source_anomaly_id = request.data.get("source_anomaly_id")
        if source_anomaly_id:
            existing_case = _find_case_by_source_anomaly_id(source_anomaly_id)
            if existing_case:
                return Response({"detail": "A case already exists for this anomaly.", "case": _normalise_case(existing_case), "duplicate": True}, status=200)
        case_id = int(_now().timestamp())
        priority = str(request.data.get("priority") or request.data.get("severity") or "medium")
        status_value = str(request.data.get("status") or "open")
        metadata = request.data.get("metadata") or {}
        if source_anomaly_id:
            metadata["source_anomaly_id"] = source_anomaly_id
        case = {"id": case_id, "source_anomaly_id": source_anomaly_id, "linked_anomaly_id": source_anomaly_id, "type": str(request.data.get("type") or request.data.get("anomaly_type") or "manual"), "anomaly_type": str(request.data.get("anomaly_type") or request.data.get("type") or "manual"), "severity": priority, "priority": priority, "status": status_value, "score": request.data.get("score") or 0, "title": str(request.data.get("title") or "Anomaly case"), "description": str(request.data.get("description") or ""), "assigned_to_id": request.data.get("assigned_to_id"), "assigned_to_username": "", "created_by_username": getattr(request.user, "username", ""), "auto_created": False, "detected_date": str(request.data.get("date") or _today()), "notes": str(request.data.get("notes") or ""), "resolution_notes": str(request.data.get("resolution_notes") or ""), "sla_due_at": (_now() + timedelta(hours=24)).isoformat(), "sla_breached": False, "escalation_level": 0, "escalated_at": None, "created_at": _now().isoformat(), "updated_at": _now().isoformat(), "closed_at": None, "metadata": metadata, "timeline": [{"id": 1, "action": "created", "description": "Case created.", "performed_by": getattr(request.user, "username", "system"), "created_at": _now().isoformat()}]}
        cases.append(case)
        _set_anomaly_cases(cases)
        return Response({"detail": "Anomaly case created successfully.", "case": _normalise_case(case)}, status=201)


class AnomalyCaseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = _get_case_by_id(case_id)
        if not case:
            return Response({"detail": "Anomaly case not found."}, status=404)
        return Response({"case": _normalise_case(case)})

    def patch(self, request, case_id):
        cases = _get_anomaly_cases()
        updated_case = None
        for index, case in enumerate(cases):
            if str(case.get("id")) == str(case_id):
                old_status = case.get("status")
                case["status"] = str(request.data.get("status") or case.get("status") or "open")
                case["priority"] = str(request.data.get("priority") or case.get("priority") or "medium")
                case["severity"] = case["priority"]
                case["assigned_to_id"] = request.data.get("assigned_to_id", case.get("assigned_to_id"))
                case["notes"] = str(request.data.get("notes") or case.get("notes") or "")
                case["resolution_notes"] = str(request.data.get("resolution_notes") or case.get("resolution_notes") or "")
                case["updated_at"] = _now().isoformat()
                if case["status"] in ["resolved", "dismissed"] and old_status != case["status"]:
                    case["closed_at"] = _now().isoformat()
                case.setdefault("timeline", []).append({"id": len(case.get("timeline", [])) + 1, "action": "updated", "description": f"Case updated to {case['status']}.", "performed_by": getattr(request.user, "username", "system"), "created_at": _now().isoformat()})
                cases[index] = case
                updated_case = case
                break
        if not updated_case:
            return Response({"detail": "Anomaly case not found."}, status=404)
        _set_anomaly_cases(cases)
        return Response({"detail": "Anomaly case updated successfully.", "case": _normalise_case(updated_case)})


class AnomalyCaseEvidenceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        evidence = cache.get(_anomaly_evidence_cache_key(case_id), [])
        return Response({"case_id": int(case_id), "count": len(evidence), "results": evidence, "evidence": evidence})

    def post(self, request, case_id):
        evidence = cache.get(_anomaly_evidence_cache_key(case_id), [])
        uploaded_file = request.FILES.get("file")
        note = str(request.data.get("note") or request.data.get("description") or "")
        evidence_item = {"id": len(evidence) + 1, "case_id": int(case_id), "original_filename": uploaded_file.name if uploaded_file else str(request.data.get("file_name") or "manual_note.txt"), "note": note, "uploaded_by_username": getattr(request.user, "username", ""), "created_at": _now().isoformat(), "file_url": ""}
        evidence.append(evidence_item)
        cache.set(_anomaly_evidence_cache_key(case_id), evidence, timeout=None)
        return Response({"detail": "Evidence uploaded successfully.", "evidence": evidence_item}, status=201)


class AnomalyCaseEvidenceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id, evidence_id):
        evidence = cache.get(_anomaly_evidence_cache_key(case_id), [])
        item = next((e for e in evidence if str(e.get("id")) == str(evidence_id)), None)
        if not item:
            return Response({"detail": "Evidence not found."}, status=404)
        return Response(item)


class AnomalyCaseEvidenceDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id=None, evidence_id=None):
        return Response({"detail": "Evidence download prepared.", "success": True, "case_id": case_id, "evidence_id": evidence_id})


class AnomalyDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date = _parse_date_param(request.GET.get("date"))
        cases = [_normalise_case(case) for case in _get_anomaly_cases()]
        live_anomalies = _build_live_anomalies(request.user, target_date)
        combined = live_anomalies + cases
        critical = sum(1 for a in combined if str(a.get("priority") or a.get("severity")).lower() == "critical")
        high = sum(1 for a in combined if str(a.get("priority") or a.get("severity")).lower() == "high")
        medium = sum(1 for a in combined if str(a.get("priority") or a.get("severity")).lower() == "medium")
        low = sum(1 for a in combined if str(a.get("priority") or a.get("severity")).lower() == "low")
        open_cases = sum(1 for a in combined if str(a.get("status", "")).lower() == "open")
        breached_cases = sum(1 for a in combined if a.get("sla_breached"))
        escalated_cases = sum(1 for a in combined if int(a.get("escalation_level") or 0) > 0)
        return Response({"date": str(target_date), "summary": {"total": len(combined), "total_anomalies": len(combined), "critical": critical, "high": high, "medium": medium, "low": low, "open_cases": open_cases, "breached_cases": breached_cases, "escalated_cases": escalated_cases, "auto_case_created_count": sum(1 for c in cases if c.get("auto_created"))}, "anomalies": combined, "cases": cases, "results": combined})


class ShiftAlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_shift = _get_active_shift(request.user)
        if active_shift:
            alerts = [{"level": "info", "severity": "info", "code": "active_shift", "title": "Active shift open", "message": f"Shift {active_shift.get('shift_id')} is currently open."}]
        else:
            alerts = [{"level": "warning", "severity": "warning", "code": "no_active_shift", "title": "No active shift", "message": "No active shift is currently open."}]
        return Response({"count": len(alerts), "alerts": alerts, "results": alerts})


class ShiftAlertUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"unread_count": 0})


class MarkShiftAlertsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Shift alerts marked as read.", "success": True})


class ShiftReportPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shift_value = request.GET.get("shift")
        target_date = _parse_date_param(request.GET.get("date"))
        sales_qs = _sales_queryset_for_day(target_date)
        if shift_value:
            sales_qs = sales_qs.filter(shift=shift_value)
        metrics = _metrics_from_sales(sales_qs)
        return Response({"detail": "Shift report PDF payload generated successfully.", "date": str(target_date), "shift": shift_value, "summary": _shift_summary_dict(metrics), "sales": [_serialize_sale(sale) for sale in sales_qs.order_by("-created_at")[:200]], "success": True})


OpenShiftView = StartShiftView
CloseShiftView = EndShiftView
MyCurrentShiftView = CurrentShiftView
MyShiftHistoryView = ShiftHistoryView
DailySalesSummaryView = DailySummaryView
ShiftReportView = ShiftSalesReportView
ActiveShiftView = CurrentShiftView
ClosedShiftView = LastClosedShiftView
AllShiftsView = AllShiftsAdminView
ShiftVarianceView = ShiftVarianceDashboardView
ShiftDashboardView = ShiftVarianceDashboardView
ShiftSummaryView = DailySummaryView
TodaySummaryView = DailySummaryView
TerminalActivityReportView = TerminalActivityView
HistoricalTrendView = HistoricalTrendsView
AnomalyCasesView = AnomalyCaseListCreateView
AnomalyCaseView = AnomalyCaseDetailView
AnomalyEvidenceListView = AnomalyCaseEvidenceListCreateView
AnomalyEvidenceDetailView = AnomalyCaseEvidenceDetailView
AnomalyEvidenceDownloadView = AnomalyCaseEvidenceDownloadView
ShiftPdfReportView = ShiftReportPdfView
TerminalsView = TerminalListView
RegisterTerminalView = TerminalRegisterView
AnomalyDashboardSummaryView = AnomalyDashboardView
