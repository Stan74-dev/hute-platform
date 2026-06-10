from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.sales.models import Sale, Refund


def safe_sum(queryset, field_name):
    try:
        return queryset.aggregate(v=Sum(field_name))["v"] or Decimal("0.00")
    except Exception:
        return Decimal("0.00")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_mobile_dashboard(request):
    today = timezone.localdate()
    start = request.query_params.get("start")
    end = request.query_params.get("end")

    sales = Sale.objects.all()
    refunds = Refund.objects.all()

    if start:
        sales = sales.filter(created_at__date__gte=start)
        refunds = refunds.filter(created_at__date__gte=start)
    else:
        sales = sales.filter(created_at__date=today)
        refunds = refunds.filter(created_at__date=today)

    if end:
        sales = sales.filter(created_at__date__lte=end)
        refunds = refunds.filter(created_at__date__lte=end)

    total_sales = safe_sum(sales, "total_amount")
    total_profit = safe_sum(sales, "total_profit")
    cash_sales = sales.filter(payment_method__icontains="cash")
    card_sales = sales.filter(payment_method__icontains="card")

    refunds_total = (
        safe_sum(refunds, "total_refund_amount")
        or safe_sum(refunds, "total_amount")
        or safe_sum(refunds, "amount")
    )

    return Response({
        "date": str(today),
        "total_sales": total_sales,
        "transaction_count": sales.count(),
        "cash_sales": safe_sum(cash_sales, "total_amount"),
        "card_sales": safe_sum(card_sales, "total_amount"),
        "total_profit": total_profit,
        "refunds_total": refunds_total,
        "anomalies_count": 0,
    })