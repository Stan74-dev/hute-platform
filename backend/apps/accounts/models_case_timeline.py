from django.conf import settings
from django.db import models


class AnomalyCaseTimeline(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("status_changed", "Status Changed"),
        ("assigned", "Assigned"),
        ("unassigned", "Unassigned"),
        ("priority_changed", "Priority Changed"),
        ("note_updated", "Note Updated"),
        ("resolution_updated", "Resolution Updated"),
        ("evidence_added", "Evidence Added"),
        ("sla_set", "SLA Set"),
        ("sla_breached", "SLA Breached"),
        ("escalated", "Escalated"),
    ]

    case = models.ForeignKey(
        "accounts.AnomalyCase",
        on_delete=models.CASCADE,
        related_name="timeline_events",
        db_index=True,
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="performed_anomaly_case_timeline_events",
        db_index=True,
    )
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.case_id} - {self.action}"