from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.finance.models import SupplierInvoice
from apps.finance.models_tax import TaxRate
from apps.sales.models import Sale


class TaxRateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rates = TaxRate.objects.filter(is_active=True).order_by("name")
        return Response(
            {
                "rates": [
                    {
                        "id": rate.id,
                        "name": rate.name,
                        "code": rate.code,
                        "rate_percent": str(rate.rate_percent),
                        "tax_type": rate.tax_type,
                        "category": rate.category,
                        "is_default": rate.is_default,
                    }
                    for rate in rates
                ]
            }
        )


class TaxSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        sales = Sale.objects.all()
        purchase_invoices = SupplierInvoice.objects.all()

        if date_from:
          sales = sales.filter(created_at__date__gte=date_from)
          purchase_invoices = purchase_invoices.filter(invoice_date__gte=date_from)

        if date_to:
          sales = sales.filter(created_at__date__lte=date_to)
          purchase_invoices = purchase_invoices.filter(invoice_date__lte=date_to)

        output_net_sales = Decimal("0.00")
        output_tax = Decimal("0.00")
        output_gross_sales = Decimal("0.00")

        for sale in sales:
            output_net_sales += Decimal(str(getattr(sale, "subtotal", 0) or 0))
            output_tax += Decimal(str(getattr(sale, "tax_total", 0) or 0))
            output_gross_sales += Decimal(
                str(getattr(sale, "grand_total", getattr(sale, "total_amount", 0)) or 0)
            )

        input_net_purchases = Decimal("0.00")
        input_tax = Decimal("0.00")
        input_gross_purchases = Decimal("0.00")

        for invoice in purchase_invoices:
            input_net_purchases += Decimal(str(getattr(invoice, "subtotal_amount", 0) or 0))
            input_tax += Decimal(str(getattr(invoice, "tax_amount", 0) or 0))
            input_gross_purchases += Decimal(str(getattr(invoice, "total_amount", 0) or 0))

        net_vat_payable = output_tax - input_tax

        return Response(
            {
                "summary": {
                    "sales_count": sales.count(),
                    "purchase_invoice_count": purchase_invoices.count(),
                    "output_net_sales": str(output_net_sales),
                    "output_tax": str(output_tax),
                    "output_gross_sales": str(output_gross_sales),
                    "input_net_purchases": str(input_net_purchases),
                    "input_tax": str(input_tax),
                    "input_gross_purchases": str(input_gross_purchases),
                    "net_vat_payable": str(net_vat_payable),
                }
            }
        )