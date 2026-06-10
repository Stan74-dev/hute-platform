from django.db import models
class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=80)
    symbol = models.CharField(max_length=10, blank=True)
    is_base = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.code
class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_from")
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_to")
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    effective_date = models.DateField()
    source = models.CharField(max_length=120, blank=True)
    locked_for_day = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ("from_currency", "to_currency", "effective_date")
class SplitTender(models.Model):
    sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.SET_NULL, related_name="split_tenders")
    base_currency = models.CharField(max_length=10, default="USD")
    base_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_balanced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
class SplitTenderLine(models.Model):
    tender = models.ForeignKey(SplitTender, on_delete=models.CASCADE, related_name="lines")
    currency = models.CharField(max_length=10)
    payment_method = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    exchange_rate_to_base = models.DecimalField(max_digits=18, decimal_places=6, default=1)
    base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
