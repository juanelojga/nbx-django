import graphene
from graphene_django import DjangoObjectType
from .models import Package

class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = "__all__"

class Query(graphene.ObjectType):
    all_packages = graphene.List(PackageType)
    package = graphene.Field(PackageType, id=graphene.Int())

    def resolve_all_packages(root, info):
        return Package.objects.all()

    def resolve_package(root, info, id):
        return Package.objects.get(pk=id)

schema = graphene.Schema(query=Query)
