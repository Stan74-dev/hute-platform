from django.db import models
from products.models import Product


class Warehouse(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}"


# OPTIONAL (only if you want transfers)
class StockTransfer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    from_warehouse = models.ForeignKey(Warehouse, related_name="from_wh", on_delete=models.CASCADE)
    to_warehouse = models.ForeignKey(Warehouse, related_name="to_wh", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"