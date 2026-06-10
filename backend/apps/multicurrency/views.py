from decimal import Decimal
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Currency, ExchangeRate, SplitTender
from .serializers import CurrencySerializer, ExchangeRateSerializer, SplitTenderSerializer
class CurrencyViewSet(viewsets.ModelViewSet): queryset = Currency.objects.all(); serializer_class = CurrencySerializer; permission_classes = [permissions.IsAuthenticated]
class ExchangeRateViewSet(viewsets.ModelViewSet): queryset = ExchangeRate.objects.all(); serializer_class = ExchangeRateSerializer; permission_classes = [permissions.IsAuthenticated]
class SplitTenderViewSet(viewsets.ReadOnlyModelViewSet): queryset = SplitTender.objects.all(); serializer_class = SplitTenderSerializer; permission_classes = [permissions.IsAuthenticated]
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def calculate_split_tender(request):
    base_total = Decimal(str(request.data.get("base_total", "0")))
    total_base_paid = Decimal("0.00")
    calculated_lines = []
    for line in request.data.get("lines", []):
        amount = Decimal(str(line.get("amount", "0")))
        rate = Decimal(str(line.get("exchange_rate_to_base", "1")))
        base_amount = amount * rate
        total_base_paid += base_amount
        calculated_lines.append({**line, "base_amount": str(base_amount.quantize(Decimal("0.01")))})
    balance = base_total - total_base_paid
    return Response({"base_total": str(base_total.quantize(Decimal("0.01"))), "base_paid": str(total_base_paid.quantize(Decimal("0.01"))), "balance": str(balance.quantize(Decimal("0.01"))), "is_balanced": abs(balance) <= Decimal("0.01"), "lines": calculated_lines})
