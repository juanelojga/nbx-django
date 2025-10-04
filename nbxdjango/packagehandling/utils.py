from django.conf import settings
from django_q.tasks import async_task


def send_email(subject, body, recipient_list):
    """
    A utility function to send emails asynchronously.
    """
    async_task(
        "django.core.mail.send_mail",
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )
