from django.contrib.auth.models import User
from django.db import models
from apps.common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("cashier", "Cashier"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="cashier")

    def __str__(self):
        return f"{self.user.username} ({self.role})"