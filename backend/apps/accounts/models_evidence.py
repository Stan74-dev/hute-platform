from django.conf import settings
from django.db import models


def anomaly_case_evidence_upload_path(instance, filename):
    case_id = instance.case_id or "unassigned"
    return f"anomaly_case_evidence/case_{case_id}/{filename}"


class AnomalyCaseEvidence(models.Model):
    case = models.ForeignKey(
        "accounts.AnomalyCase",
        on_delete=models.CASCADE,
        related_name="evidence_items",
        db_index=True,
    )
    file = models.FileField(upload_to=anomaly_case_evidence_upload_path)
    original_filename = models.CharField(max_length=255, blank=True, default="", db_index=True)
    note = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_anomaly_evidence",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "-created_at"]),
        ]

    def __str__(self):
        return self.original_filename or self.file.name