from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.sales.models import Sale, Refund

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

    totals = sales.aggregate(
        total_sales=Sum("total_amount"),
        transaction_count=Count("id"),
        total_profit=Sum("total_profit"),
    )

    cash_sales = sales.filter(payment_method__icontains="cash").aggregate(v=Sum("total_amount"))["v"] or Decimal("0.00")
    card_sales = sales.filter(payment_method__icontains="card").aggregate(v=Sum("total_amount"))["v"] or Decimal("0.00")
    refunds_total = refunds.aggregate(v=Sum("total_refund_amount"))["v"] or Decimal("0.00")

    return Response({
        "date": str(today),
        "total_sales": totals.get("total_sales") or Decimal("0.00"),
        "transaction_count": totals.get("transaction_count") or 0,
        "cash_sales": cash_sales,
        "card_sales": card_sales,
        "total_profit": totals.get("total_profit") or Decimal("0.00"),
        "refunds_total": refunds_total,
        "anomalies_count": 0,
    })
