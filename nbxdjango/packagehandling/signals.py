from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Client

@receiver(post_save, sender=Client)
def add_user_to_client_group(sender, instance, created, **kwargs):
    if created and instance.user:
        try:
            client_group = Group.objects.get(name='Client')
            instance.user.groups.add(client_group)
        except Group.DoesNotExist:
            pass
