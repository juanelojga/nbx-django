import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from ..models import Client, Consolidate, Package


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "username", "first_name", "last_name", "is_active", "date_joined")
        # Explicitly exclude: password, is_superuser, is_staff, groups, user_permissions


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
            "comments",
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


class ClientConnection(graphene.ObjectType):
    results = graphene.List(ClientType)
    total_count = graphene.Int()
    page = graphene.Int()
    page_size = graphene.Int()
    has_next = graphene.Boolean()
    has_previous = graphene.Boolean()


class ConsolidateType(DjangoObjectType):
    class Meta:
        model = Consolidate
        fields = (
            "id",
            "description",
            "status",
            "delivery_date",
            "comment",
            "extra_attributes",
            "created_at",
            "updated_at",
            "client",
            "packages",
        )


class PackageConnection(graphene.ObjectType):
    results = graphene.List(PackageType)
    total_count = graphene.Int()
    page = graphene.Int()
    page_size = graphene.Int()
    has_next = graphene.Boolean()
    has_previous = graphene.Boolean()


class ConsolidateConnection(graphene.ObjectType):
    results = graphene.List(ConsolidateType)
    total_count = graphene.Int()
    page = graphene.Int()
    page_size = graphene.Int()
    has_next = graphene.Boolean()
    has_previous = graphene.Boolean()
