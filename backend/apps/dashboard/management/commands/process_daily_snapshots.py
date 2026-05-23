from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum

from apps.accounts.models_case import AnomalyCase
from apps.accounts.models_anomaly import AnomalyScanRun
from apps.accounts.models_shift import CashierShift
from apps.dashboard.models_snapshot import DailyMetricSnapshot
from apps.sales.models import Sale


def as_decimal(value):
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


class Command(BaseCommand):
    help = "Builds or refreshes daily metric snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")

    def handle(self, *args, **options):
        if options.get("date"):
            target_date = timezone.datetime.strptime(options["date"], "%Y-%m-%d").date()
        else:
            target_date = timezone.localdate()

        sales_qs = Sale.objects.filter(created_at__date=target_date)
        shifts_qs = CashierShift.objects.filter(closed_at__date=target_date, status="closed")

        latest_scan = (
            AnomalyScanRun.objects
            .filter(scan_date=target_date, status="completed")
            .order_by("-completed_at", "-started_at")
            .first()
        )

        total_sales = as_decimal(sales_qs.aggregate(total=Sum("total_amount"))["total"])
        total_profit = as_decimal(sales_qs.aggregate(total=Sum("total_profit"))["total"])
        total_transactions = sales_qs.count()
        closed_shifts = shifts_qs.count()

        anomaly_count = 0
        critical_anomaly_count = 0
        high_anomaly_count = 0
        medium_anomaly_count = 0
        low_anomaly_count = 0

        if latest_scan:
            anomalies_qs = latest_scan.anomalies.all()
            anomaly_count = anomalies_qs.count()
            critical_anomaly_count = anomalies_qs.filter(severity="critical").count()
            high_anomaly_count = anomalies_qs.filter(severity="high").count()
            medium_anomaly_count = anomalies_qs.filter(severity="medium").count()
            low_anomaly_count = anomalies_qs.filter(severity="low").count()

        open_case_count = AnomalyCase.objects.filter(status__in=["open", "investigating"]).count()
        breached_case_count = AnomalyCase.objects.filter(status__in=["open", "investigating"], sla_breached=True).count()
        escalated_case_count = AnomalyCase.objects.filter(status__in=["open", "investigating"], escalation_level__gt=0).count()

        snapshot, created = DailyMetricSnapshot.objects.update_or_create(
            snapshot_date=target_date,
            defaults={
                "total_sales": total_sales,
                "total_profit": total_profit,
                "total_transactions": total_transactions,
                "closed_shifts": closed_shifts,
                "anomaly_count": anomaly_count,
                "critical_anomaly_count": critical_anomaly_count,
                "high_anomaly_count": high_anomaly_count,
                "medium_anomaly_count": medium_anomaly_count,
                "low_anomaly_count": low_anomaly_count,
                "open_case_count": open_case_count,
                "breached_case_count": breached_case_count,
                "escalated_case_count": escalated_case_count,
            },
        )

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Daily snapshot {action} for {target_date}"
            )
        )