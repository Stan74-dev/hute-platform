from django.db import models


class AnomalyScanRun(models.Model):
    scan_date = models.DateField(db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    anomaly_count = models.PositiveIntegerField(default=0)
    auto_case_created_count = models.PositiveIntegerField(default=0)
    auto_case_reused_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="running")

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.scan_date} ({self.status})"


class StoredAnomaly(models.Model):
    run = models.ForeignKey(
        AnomalyScanRun,
        on_delete=models.CASCADE,
        related_name="anomalies",
    )
    anomaly_date = models.DateField(db_index=True)
    anomaly_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, db_index=True)
    score = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    source_reference = models.CharField(max_length=255, blank=True, default="", db_index=True)

    case = models.ForeignKey(
        "accounts.AnomalyCase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stored_anomalies",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "title"]

    def __str__(self):
        return f"{self.anomaly_date} - {self.anomaly_type} - {self.title}"