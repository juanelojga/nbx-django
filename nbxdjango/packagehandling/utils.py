from django.core.mail import send_mail
from django.conf import settings

def send_email(subject, body, recipient_list):
    """
    A utility function to send emails.
    """
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )
