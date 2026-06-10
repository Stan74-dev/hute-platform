import os
from decimal import Decimal
from django.utils import timezone
from .models import FiscalInvoice, FiscalSubmissionLog, FiscalStatus

def build_fiscal_payload(invoice):
    return {
        "invoiceNumber": invoice.invoice_number,
        "currency": invoice.currency,
        "grossTotal": str(invoice.gross_total),
        "taxTotal": str(invoice.tax_total),
        "netTotal": str(invoice.net_total),
        "buyer": {"name": invoice.buyer_name, "taxNumber": invoice.buyer_tax_number},
        "saleId": invoice.sale_id,
    }

def submit_invoice_to_fiscal_provider(invoice):
    payload = build_fiscal_payload(invoice)
    invoice.request_payload = payload
    invoice.status = FiscalStatus.SUBMITTED
    invoice.submitted_at = timezone.now()
    invoice.save()
    provider = os.environ.get("FISCAL_PROVIDER", "sandbox")
    if provider == "sandbox":
        response = {
            "accepted": True,
            "fiscalDayNumber": "SANDBOX-DAY",
            "fiscalReceiptNumber": f"FISC-{invoice.invoice_number}",
            "fiscalSignature": "SANDBOX-SIGNATURE",
            "qrData": f"HUTE-FISCAL-SANDBOX:{invoice.invoice_number}",
        }
    else:
        response = {"accepted": False, "error": "Fiscal provider API not configured yet"}
    invoice.response_payload = response
    if response.get("accepted"):
        invoice.status = FiscalStatus.ACCEPTED
        invoice.fiscal_day_number = response.get("fiscalDayNumber", "")
        invoice.fiscal_receipt_number = response.get("fiscalReceiptNumber", "")
        invoice.fiscal_signature = response.get("fiscalSignature", "")
        invoice.fiscal_qr_data = response.get("qrData", "")
    else:
        invoice.status = FiscalStatus.FAILED
        invoice.error_message = response.get("error", "Fiscal submission failed")
    invoice.save()
    FiscalSubmissionLog.objects.create(invoice=invoice, status=invoice.status, message=invoice.error_message or "Fiscal submission processed", payload=response)
    return invoice

def create_invoice_from_sale(sale, user=None):
    total = getattr(sale, "total_amount", Decimal("0.00")) or Decimal("0.00")
    tax = getattr(sale, "tax_amount", Decimal("0.00")) or Decimal("0.00")
    return FiscalInvoice.objects.create(
        sale=sale,
        invoice_number=f"INV-{sale.id}",
        currency=getattr(sale, "currency", "USD") or "USD",
        gross_total=total,
        tax_total=tax,
        net_total=total-tax,
        created_by=user,
    )
