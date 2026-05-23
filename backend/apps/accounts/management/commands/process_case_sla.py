from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models_case import AnomalyCase
from apps.accounts.models_case_timeline import AnomalyCaseTimeline


def should_case_be_closed(case_obj):
    return case_obj.status in ["resolved", "dismissed"]


def get_sla_hours(priority):
    mapping = {
        "low": 72,
        "medium": 24,
        "high": 8,
        "critical": 2,
    }
    return mapping.get(priority or "medium", 24)


def evaluate_case_sla(case_obj):
    now = timezone.now()

    if should_case_be_closed(case_obj):
        changed = False
        if case_obj.sla_breached:
            case_obj.sla_breached = False
            changed = True
        if changed:
            case_obj.save(update_fields=["sla_breached", "updated_at"])
        return "closed_reset" if changed else "closed_ok"

    if case_obj.sla_due_at and now > case_obj.sla_due_at:
        if not case_obj.sla_breached:
            case_obj.sla_breached = True
            case_obj.save(update_fields=["sla_breached", "updated_at"])
            return "breached_now"
        return "already_breached"

    if case_obj.sla_breached:
        case_obj.sla_breached = False
        case_obj.save(update_fields=["sla_breached", "updated_at"])
        return "restored"

    return "healthy"


def maybe_escalate_case(case_obj):
    if should_case_be_closed(case_obj):
        return None

    if not case_obj.sla_due_at:
        return None

    now = timezone.now()
    if now <= case_obj.sla_due_at:
        return None

    overdue = now - case_obj.sla_due_at
    new_level = 0

    if overdue >= timedelta(hours=24):
        new_level = 3
    elif overdue >= timedelta(hours=8):
        new_level = 2
    elif overdue >= timedelta(minutes=1):
        new_level = 1

    if new_level > case_obj.escalation_level:
        old_level = case_obj.escalation_level
        case_obj.escalation_level = new_level
        case_obj.escalated_at = now
        case_obj.sla_breached = True
        case_obj.save(update_fields=["escalation_level", "escalated_at", "sla_breached", "updated_at"])

        if old_level == 0:
            AnomalyCaseTimeline.objects.create(
                case=case_obj,
                action="sla_breached",
                description="SLA breached",
                performed_by=None,
                metadata={
                    "sla_due_at": str(case_obj.sla_due_at),
                    "new_escalation_level": new_level,
                },
            )

        AnomalyCaseTimeline.objects.create(
            case=case_obj,
            action="escalated",
            description=f"Escalated to level {new_level}",
            performed_by=None,
            metadata={
                "old_escalation_level": old_level,
                "new_escalation_level": new_level,
                "sla_due_at": str(case_obj.sla_due_at),
            },
        )
        return new_level

    return None


class Command(BaseCommand):
    help = "Processes anomaly case SLA breaches and escalation levels."

    def handle(self, *args, **options):
        queryset = (
            AnomalyCase.objects
            .filter(status__in=["open", "investigating"])
            .order_by("sla_due_at", "created_at")
        )

        checked = 0
        breached_now = 0
        escalated = 0

        for case_obj in queryset.iterator():
            checked += 1

            sla_result = evaluate_case_sla(case_obj)
            if sla_result == "breached_now":
                breached_now += 1

            escalation_result = maybe_escalate_case(case_obj)
            if escalation_result is not None:
                escalated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"SLA processing complete. checked={checked}, newly_breached={breached_now}, escalated={escalated}"
            )
        )