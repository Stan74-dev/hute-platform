from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CashierShift(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    terminal_id = models.CharField(max_length=100)

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    opening_float = models.DecimalField(max_digits=10, decimal_places=2)

    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    variance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")

    def __str__(self):
        return f"{self.user.username} - {self.status}"