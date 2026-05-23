from django.db import models

class Sale(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField(default=0)
    total_profit = models.FloatField(default=0)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    cost_price = models.FloatField()
    profit = models.FloatField()


class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, default="CASH")