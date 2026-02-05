from django.conf import settings
from django.template.loader import render_to_string
from django_q.tasks import async_task

from .emails.messages import CONSOLIDATION_NOTIFICATION_SUBJECT


def send_email(subject, body, recipient_list, html_message=None):
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
        html_message=html_message,
    )


def send_consolidation_notification_email(consolidation):
    """
    Send an email notification to the client when their packages
    have arrived in Panama and are ready for pickup.

    Args:
        consolidation: A Consolidate model instance with related packages
    """
    from .models import Consolidate  # Avoid circular import

    # Get the consolidation with related packages
    if isinstance(consolidation, Consolidate):
        consolidate_obj = consolidation
    else:
        consolidate_obj = Consolidate.objects.prefetch_related("packages").get(pk=consolidation)

    client = consolidate_obj.client

    # Calculate total cost from packages
    packages = list(consolidate_obj.packages.all())
    total_cost = sum(pkg.service_price or 0 for pkg in packages)

    # Prepare context for the email template
    context = {
        "client_name": client.full_name,
        "packages": packages,
        "total_cost": total_cost,
        "logo_url": getattr(settings, "NARBOX_LOGO_URL", ""),
    }

    # Render the HTML email
    html_message = render_to_string(
        "packagehandling/emails/consolidation_notification.html",
        context,
    )

    # Plain text version (fallback)
    plain_message = f"""
Estimado(a) Cliente:

{client.full_name.upper()}

Hola! Tu paquetes llegaron a Panamá y están disponibles para ser retirados.

Paquetes:
"""
    for pkg in packages:
        plain_message += f"- TRACKING {pkg.barcode} - {pkg.courier}"
        if pkg.weight:
            plain_message += f" - Peso: {pkg.weight} {pkg.weight_unit or 'lb'}"
        if pkg.service_price:
            plain_message += f" - Costo: ${pkg.service_price}"
        plain_message += "\n"

    plain_message += f"""
El total a cancelar será de ${total_cost:.2f}

Puedes realizar tus pagos de flete bajo las siguientes alternativas:
- Pago por punto de venta en nuestras oficinas.
- Transferencia (ACH) o pago en efectivo a nuestra cuenta corriente no. 0349010555030 "
"del Banco General a nombre de Servicios de Corretaje y Transporte S.A.

Cuando nos depositan enviarnos el comprobante a nuestro correo narbox@sercotran.com o al whatsapp 6612-6130.

Atentamente,
Narboxcourier

Su paquete con los mejores
"""

    # Send the email to the client's email
    send_email(
        subject=CONSOLIDATION_NOTIFICATION_SUBJECT,
        body=plain_message,
        recipient_list=[client.email],
        html_message=html_message,
    )
