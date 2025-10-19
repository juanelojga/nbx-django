from django.db import models

from .client import Client
from .package import Package


class Consolidate(models.Model):
    description = models.TextField()
    status = models.CharField(max_length=255)
    delivery_date = models.DateField()
    comment = models.TextField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="consolidates")
    packages = models.ManyToManyField(Package, related_name="consolidates")
    extra_attributes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consolidate {self.id} for {self.client}"
