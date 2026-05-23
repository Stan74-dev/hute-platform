from django.db import models


class DailyMetricSnapshot(models.Model):
    snapshot_date = models.DateField(unique=True, db_index=True)

    total_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    closed_shifts = models.PositiveIntegerField(default=0)

    anomaly_count = models.PositiveIntegerField(default=0)
    critical_anomaly_count = models.PositiveIntegerField(default=0)
    high_anomaly_count = models.PositiveIntegerField(default=0)
    medium_anomaly_count = models.PositiveIntegerField(default=0)
    low_anomaly_count = models.PositiveIntegerField(default=0)

    open_case_count = models.PositiveIntegerField(default=0)
    breached_case_count = models.PositiveIntegerField(default=0)
    escalated_case_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-snapshot_date"]

    def __str__(self):
        return f"Daily Snapshot {self.snapshot_date}"