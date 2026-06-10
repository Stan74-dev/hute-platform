from django.conf import settings
from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    manager_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

class BranchTerminal(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="terminals")
    terminal_name = models.CharField(max_length=120)
    terminal_code = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.branch.code} - {self.terminal_name}"
