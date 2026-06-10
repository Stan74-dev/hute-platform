from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.sales.models import Sale
from .models import FiscalDevice, FiscalInvoice
from .serializers import FiscalDeviceSerializer, FiscalInvoiceSerializer
from .services import create_invoice_from_sale, submit_invoice_to_fiscal_provider

class FiscalDeviceViewSet(viewsets.ModelViewSet):
    queryset = FiscalDevice.objects.all()
    serializer_class = FiscalDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
class FiscalInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FiscalInvoice.objects.select_related("sale").all()
    serializer_class = FiscalInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def fiscalise_sale(request, sale_id):
    try: sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist: return Response({"detail": "Sale not found"}, status=status.HTTP_404_NOT_FOUND)
    invoice = FiscalInvoice.objects.filter(sale=sale).first() or create_invoice_from_sale(sale, request.user)
    invoice = submit_invoice_to_fiscal_provider(invoice)
    return Response(FiscalInvoiceSerializer(invoice).data)
