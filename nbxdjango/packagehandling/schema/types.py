import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from ..models import Package, Client


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = "__all__"

class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = (
            "id",
            "barcode",
            "courier",
            "other_courier",
            "length",
            "width",
            "height",
            "dimension_unit",
            "weight",
            "weight_unit",
            "description",
            "purchase_link",
            "real_price",
            "service_price",
            "arrival_date",
            "created_at",
            "updated_at",
            "client",
        )


class ClientType(DjangoObjectType):
    class Meta:
        model = Client
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "identification_number",
            "state",
            "city",
            "main_street",
            "secondary_street",
            "building_number",
            "mobile_phone_number",
            "phone_number",
            "created_at",
            "updated_at",
            "user",
        )
