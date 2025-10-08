from django.db import models

from .client import Client


class Package(models.Model):
    barcode = models.CharField(max_length=255)
    courier = models.CharField(max_length=255)
    other_courier = models.CharField(max_length=255, null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    dimension_unit = models.CharField(max_length=10, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    weight_unit = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    purchase_link = models.URLField(null=True, blank=True)
    real_price = models.FloatField(null=True, blank=True)
    service_price = models.FloatField(null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="packages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Package {self.barcode}"
