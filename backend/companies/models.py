from django.db import models


class Company(models.Model):

    name = models.CharField(max_length=255)

    email = models.EmailField()

    phone = models.CharField(max_length=50)

    address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name