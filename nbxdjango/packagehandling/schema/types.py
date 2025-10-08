import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from ..models import Client, Package


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

    full_name = graphene.String()

    def resolve_full_name(self, info):
        return self.full_name


class MeType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id", "is_superuser", "email")

    first_name = graphene.String()
    last_name = graphene.String()

    def resolve_first_name(self, info):
        if hasattr(self, "client"):
            return self.client.first_name
        return None

    def resolve_last_name(self, info):
        if hasattr(self, "client"):
            return self.client.last_name
        return None
