from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    identification_number = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    main_street = models.CharField(max_length=255)
    secondary_street = models.CharField(max_length=255)
    building_number = models.CharField(max_length=255)
    mobile_phone_number = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.full_name


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