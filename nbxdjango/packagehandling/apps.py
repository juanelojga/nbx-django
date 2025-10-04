from django.apps import AppConfig


class PackagehandlingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "packagehandling"

    def ready(self):
        import packagehandling.signals
