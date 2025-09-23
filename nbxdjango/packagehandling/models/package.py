from django.db import models
from .client import Client

class Package(models.Model):
    barcode = models.CharField(max_length=255)
    courier = models.CharField(max_length=255)
    other_courier = models.CharField(max_length=255, null=True, blank=True)
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    dimension_unit = models.CharField(max_length=10)
    weight = models.FloatField()
    weight_unit = models.CharField(max_length=10)
    description = models.TextField(null=True, blank=True)
    purchase_link = models.URLField(null=True, blank=True)
    real_price = models.FloatField()
    service_price = models.FloatField()
    arrival_date = models.DateField()
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Package {self.barcode}"
