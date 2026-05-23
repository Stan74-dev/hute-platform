from django.db import models


class TaxRate(models.Model):
    TAX_TYPE_CHOICES = [
        ("exclusive", "Exclusive"),
        ("inclusive", "Inclusive"),
    ]

    CATEGORY_CHOICES = [
        ("standard", "Standard"),
        ("zero_rated", "Zero Rated"),
        ("exempt", "Exempt"),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    rate_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default="exclusive")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="standard")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"