from django.contrib import admin

from .models import Client, Consolidate, CustomUser, Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("barcode", "courier", "client", "created_at")
    list_filter = ("courier", "created_at")
    search_fields = ("barcode", "description", "client__email")
    raw_id_fields = ("client", "consolidate")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "city", "created_at")
    search_fields = ("first_name", "last_name", "email", "identification_number")
    list_filter = ("state", "city", "created_at")


@admin.register(Consolidate)
class ConsolidateAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "status", "delivery_date", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("client__email", "description")


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_superuser", "is_active", "date_joined")
    search_fields = ("email", "username")
    list_filter = ("is_superuser", "is_active", "date_joined")
