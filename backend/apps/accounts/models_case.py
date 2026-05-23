from django.conf import settings
from django.db import models


class AnomalyCase(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    anomaly_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, default="medium", db_index=True)
    score = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    detected_date = models.DateField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    dedupe_key = models.CharField(max_length=255, blank=True, default="", db_index=True)
    source_reference = models.CharField(max_length=255, blank=True, default="", db_index=True)
    auto_created = models.BooleanField(default=False, db_index=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium", db_index=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_anomaly_cases",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_anomaly_cases",
        db_index=True,
    )

    notes = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)

    sla_due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sla_breached = models.BooleanField(default=False, db_index=True)
    escalation_level = models.PositiveIntegerField(default=0, db_index=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["priority", "-created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["sla_breached", "status"]),
            models.Index(fields=["detected_date", "anomaly_type"]),
            models.Index(fields=["source_reference", "detected_date"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"