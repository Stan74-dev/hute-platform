import os
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.utils import timezone
from apps.sales.models import Sale, Refund

class Command(BaseCommand):
    help = "Send daily HUTE sales summary by WhatsApp"

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        sales = Sale.objects.filter(created_at__date=today)
        summary = sales.aggregate(total_sales=Sum("total_amount"), total_profit=Sum("total_profit"), transaction_count=Count("id"))
        refunds_total = Refund.objects.filter(created_at__date=today).aggregate(v=Sum("total_refund_amount"))["v"] or Decimal("0.00")

        message = (
            f"HUTE Daily Report - {today}\n"
            f"Sales: {summary.get('transaction_count') or 0}\n"
            f"Total Revenue: {summary.get('total_sales') or Decimal('0.00')}\n"
            f"Gross Profit: {summary.get('total_profit') or Decimal('0.00')}\n"
            f"Refunds: {refunds_total}\n"
        )

        if os.environ.get("WHATSAPP_PROVIDER", "").lower() != "twilio":
            self.stdout.write(message)
            self.stdout.write(self.style.WARNING("WHATSAPP_PROVIDER not set to twilio. Printed report only."))
            return

        sid = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_no = os.environ.get("TWILIO_WHATSAPP_FROM")
        to_no = os.environ.get("OWNER_WHATSAPP_TO")

        if not all([sid, token, from_no, to_no]):
            self.stdout.write(self.style.ERROR("Missing Twilio WhatsApp environment variables"))
            return

        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            data={"From": from_no, "To": to_no, "Body": message},
            auth=(sid, token),
            timeout=20,
        )

        if response.status_code >= 400:
            self.stdout.write(self.style.ERROR(response.text))
            return

        self.stdout.write(self.style.SUCCESS("WhatsApp daily report sent"))
