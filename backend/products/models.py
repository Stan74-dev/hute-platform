from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    cost_price = models.FloatField()
    selling_price = models.FloatField()

    def __str__(self):
        return self.name