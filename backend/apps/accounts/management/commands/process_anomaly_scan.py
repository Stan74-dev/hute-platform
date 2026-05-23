from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models_shift import CashierShift
from apps.accounts.models_case import AnomalyCase
from apps.accounts.models_case_timeline import AnomalyCaseTimeline
from apps.accounts.models_anomaly import AnomalyScanRun, StoredAnomaly
from apps.sales.models import Sale


ALERT_THRESHOLD = Decimal("20.00")
LARGE_VARIANCE_THRESHOLD = Decimal("50.00")
VERY_LARGE_VARIANCE_THRESHOLD = Decimal("100.00")
OUT_OF_HOURS_START = 22
OUT_OF_HOURS_END = 6
SPIKE_TRANSACTION_THRESHOLD = 10
SPIKE_REVENUE_THRESHOLD = Decimal("500.00")
REPEATED_SHORT_THRESHOLD = 3
MAX_ANOMALIES = 100


def money(value):
    if value is None:
        return "0.00"
    return str(value)


def calculate_sla_due_at(priority):
    mapping = {
        "low": 72,
        "medium": 24,
        "high": 8,
        "critical": 2,
    }
    hours = mapping.get(priority or "medium", 24)
    from datetime import timedelta
    return timezone.now() + timedelta(hours=hours)


def build_anomaly_payload(anomaly_type, severity, score, title, description, metadata=None, source_reference=""):
    return {
        "type": anomaly_type,
        "severity": severity,
        "score": score,
        "title": title,
        "description": description,
        "metadata": metadata or {},
        "source_reference": source_reference,
    }


def make_anomaly_dedupe_key(target_date, anomaly_type, source_reference):
    return f"{target_date}:{anomaly_type}:{source_reference}".strip()


def auto_create_or_attach_case(anomaly, target_date):
    source_reference = anomaly.get("source_reference", "") or ""
    dedupe_key = make_anomaly_dedupe_key(target_date, anomaly["type"], source_reference)

    existing = AnomalyCase.objects.filter(dedupe_key=dedupe_key).first()
    if existing:
        return existing, False

    priority = anomaly["severity"] if anomaly["severity"] in ["low", "medium", "high", "critical"] else "medium"
    sla_due_at = calculate_sla_due_at(priority)

    case_obj = AnomalyCase.objects.create(
        anomaly_type=anomaly["type"],
        severity=anomaly["severity"],
        score=anomaly["score"],
        title=anomaly["title"],
        description=anomaly["description"],
        detected_date=target_date,
        metadata=anomaly.get("metadata") or {},
        dedupe_key=dedupe_key,
        source_reference=source_reference,
        auto_created=True,
        priority=priority,
        status="open",
        sla_due_at=sla_due_at,
        sla_breached=False,
        escalation_level=0,
    )

    AnomalyCaseTimeline.objects.create(
        case=case_obj,
        action="created",
        description="Case auto-created from anomaly detection",
        performed_by=None,
        metadata={"auto_created": True, "dedupe_key": dedupe_key, "source_reference": source_reference},
    )
    AnomalyCaseTimeline.objects.create(
        case=case_obj,
        action="sla_set",
        description=f"SLA set for priority {priority}",
        performed_by=None,
        metadata={"priority": priority, "sla_due_at": str(sla_due_at)},
    )

    return case_obj, True


class Command(BaseCommand):
    help = "Runs anomaly scan, stores anomalies, and links or auto-creates cases."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")

    def handle(self, *args, **options):
        if options.get("date"):
            target_date = timezone.datetime.strptime(options["date"], "%Y-%m-%d").date()
        else:
            target_date = timezone.localdate()

        run = AnomalyScanRun.objects.create(scan_date=target_date, status="running")

        anomalies = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        shifts_today = list(
            CashierShift.objects.select_related("user")
            .filter(status="closed", closed_at__date=target_date)
            .order_by("-closed_at")[:100]
        )
        sales_today = list(
            Sale.objects.select_related("cashier", "warehouse", "shift")
            .filter(created_at__date=target_date)
            .order_by("-created_at")[:200]
        )
        recent_closed_shifts = list(
            CashierShift.objects.select_related("user")
            .filter(status="closed")
            .order_by("-closed_at")[:100]
        )

        for shift in shifts_today:
            variance = Decimal(str(shift.variance or 0))
            variance_abs = abs(variance)

            if variance_abs >= VERY_LARGE_VARIANCE_THRESHOLD:
                severity = "critical"
                score = 95
            elif variance_abs >= LARGE_VARIANCE_THRESHOLD:
                severity = "high"
                score = 80
            else:
                continue

            anomalies.append(build_anomaly_payload(
                anomaly_type="large_shift_variance",
                severity=severity,
                score=score,
                title=f"Large shift variance detected for shift {shift.id}",
                description=f"Cashier {getattr(shift.user, 'username', '')} closed shift {shift.id} with variance £{variance} on terminal {shift.terminal_id}.",
                metadata={
                    "shift_id": shift.id,
                    "cashier_username": getattr(shift.user, "username", ""),
                    "terminal_id": shift.terminal_id,
                    "variance": money(variance),
                    "variance_abs": money(variance_abs),
                    "closed_at": str(shift.closed_at) if shift.closed_at else None,
                },
                source_reference=f"shift:{shift.id}",
            ))
            severity_counts[severity] += 1

        shortage_counts = {}
        for shift in recent_closed_shifts:
            variance = Decimal(str(shift.variance or 0))
            if variance < -ALERT_THRESHOLD:
                username = getattr(shift.user, "username", "")
                shortage_counts[username] = shortage_counts.get(username, 0) + 1

        for username, count in shortage_counts.items():
            if count >= REPEATED_SHORT_THRESHOLD:
                severity = "high" if count >= 5 else "medium"
                score = 85 if count >= 5 else 65
                anomalies.append(build_anomaly_payload(
                    anomaly_type="repeated_cashier_shortage",
                    severity=severity,
                    score=score,
                    title=f"Repeated shortages detected for {username}",
                    description=f"Cashier {username} has {count} shortage shifts in recent closed shift history.",
                    metadata={"cashier_username": username, "shortage_shift_count": count},
                    source_reference=f"cashier-shortage:{username}:{count}",
                ))
                severity_counts[severity] += 1

        for sale in sales_today[:50]:
            hour = sale.created_at.hour
            if hour >= OUT_OF_HOURS_START or hour < OUT_OF_HOURS_END:
                anomalies.append(build_anomaly_payload(
                    anomaly_type="out_of_hours_sale",
                    severity="medium",
                    score=60,
                    title=f"Out-of-hours sale detected: {sale.receipt_number}",
                    description=f"Sale {sale.receipt_number} was recorded at {sale.created_at} by {getattr(sale.cashier, 'username', '') if sale.cashier else ''}.",
                    metadata={
                        "sale_id": sale.id,
                        "receipt_number": sale.receipt_number,
                        "cashier_username": getattr(sale.cashier, "username", "") if sale.cashier else "",
                        "warehouse_name": getattr(sale.warehouse, "name", "") if sale.warehouse else "",
                        "shift_id": sale.shift_id,
                        "created_at": str(sale.created_at),
                        "total_amount": money(sale.total_amount),
                    },
                    source_reference=f"sale:{sale.id}",
                ))
                severity_counts["medium"] += 1

        cashier_daily = {}
        for sale in sales_today:
            username = getattr(sale.cashier, "username", "Unknown") if sale.cashier else "Unknown"
            cashier_daily.setdefault(username, {"transactions": 0, "revenue": Decimal("0.00")})
            cashier_daily[username]["transactions"] += 1
            cashier_daily[username]["revenue"] += Decimal(str(sale.total_amount or 0))

        for username, metrics in cashier_daily.items():
            if metrics["transactions"] >= SPIKE_TRANSACTION_THRESHOLD and metrics["revenue"] >= SPIKE_REVENUE_THRESHOLD:
                anomalies.append(build_anomaly_payload(
                    anomaly_type="cashier_sales_spike",
                    severity="medium",
                    score=70,
                    title=f"Sales spike detected for {username}",
                    description=f"Cashier {username} recorded {metrics['transactions']} transactions and revenue £{metrics['revenue']} on {target_date}.",
                    metadata={
                        "cashier_username": username,
                        "transactions": metrics["transactions"],
                        "revenue": money(metrics["revenue"]),
                        "date": str(target_date),
                    },
                    source_reference=f"cashier-spike:{username}:{target_date}",
                ))
                severity_counts["medium"] += 1

        anomalies = sorted(anomalies, key=lambda a: (-a["score"], a["title"]))[:MAX_ANOMALIES]

        created_count = 0
        reused_count = 0

        StoredAnomaly.objects.filter(anomaly_date=target_date).delete()

        for anomaly in anomalies:
            case_obj, created = auto_create_or_attach_case(anomaly, target_date)
            if created:
                created_count += 1
            else:
                reused_count += 1

            StoredAnomaly.objects.create(
                run=run,
                anomaly_date=target_date,
                anomaly_type=anomaly["type"],
                severity=anomaly["severity"],
                score=anomaly["score"],
                title=anomaly["title"],
                description=anomaly["description"],
                metadata=anomaly.get("metadata") or {},
                source_reference=anomaly.get("source_reference", "") or "",
                case=case_obj,
            )

        run.anomaly_count = len(anomalies)
        run.auto_case_created_count = created_count
        run.auto_case_reused_count = reused_count
        run.status = "completed"
        run.completed_at = timezone.now()
        run.save(update_fields=[
            "anomaly_count",
            "auto_case_created_count",
            "auto_case_reused_count",
            "status",
            "completed_at",
        ])

        self.stdout.write(
            self.style.SUCCESS(
                f"Anomaly scan complete. date={target_date}, anomalies={len(anomalies)}, created={created_count}, reused={reused_count}"
            )
        )