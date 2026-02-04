from django.db import models

from .client import Client


class Consolidate(models.Model):
    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting Payment"
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    description = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
    )
    delivery_date = models.DateField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="consolidates")
    extra_attributes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["delivery_date"]),
        ]

    def __str__(self):
        return f"Consolidate {self.id} for {self.client}"
