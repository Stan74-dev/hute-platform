from django.conf import settings
from django.db import models


class AnomalyCaseActivity(models.Model):
    case = models.ForeignKey(
        "accounts.AnomalyCase",
        on_delete=models.CASCADE,
        related_name="activity_items",
    )
    activity_type = models.CharField(max_length=100)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="anomaly_case_activities",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.activity_type} - case {self.case_id}"