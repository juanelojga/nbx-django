import graphene
from graphene_django import DjangoObjectType
from .models import Package, Client

class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = "__all__"

class ClientType(DjangoObjectType):
    class Meta:
        model = Client
        fields = "__all__"

class Query(graphene.ObjectType):
    all_packages = graphene.List(PackageType)
    package = graphene.Field(PackageType, id=graphene.Int())
    all_clients = graphene.List(ClientType)
    client = graphene.Field(ClientType, id=graphene.Int())

    def resolve_all_packages(root, info):
        return Package.objects.all()

    def resolve_package(root, info, id):
        return Package.objects.get(pk=id)

    def resolve_all_clients(root, info):
        return Client.objects.all()

    def resolve_client(root, info, id):
        return Client.objects.get(pk=id)

schema = graphene.Schema(query=Query)
