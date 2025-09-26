import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from ..models import Package, Client


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = "__all__"


class ClientType(DjangoObjectType):
    class Meta:
        model = Client
        fields = "__all__"
