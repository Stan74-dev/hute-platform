from django.conf import settings
from django.db import models
from .models_shift import CashierShift
from .models_case import AnomalyCase
from .models_evidence import AnomalyCaseEvidence
from .models_case_activity import AnomalyCaseActivity
from .models_case_timeline import AnomalyCaseTimeline


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120, blank=True, default='')
    target_id = models.CharField(max_length=120, blank=True, default='')
    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f'{self.created_at} - {actor_name} - {self.action}'


class TerminalDevice(models.Model):
    terminal_id = models.CharField(max_length=120, unique=True)
    terminal_name = models.CharField(max_length=120)
    preferred_print_mode = models.CharField(max_length=30, default='browser')
    auto_print = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    last_seen_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terminal_last_seen_devices',
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['terminal_name', 'terminal_id']

    def __str__(self):
        return f'{self.terminal_name} ({self.terminal_id})'
