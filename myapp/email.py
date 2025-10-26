from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, SendSmtpEmail, TransactionalEmailsApi, SendSmtpEmailAttachment
from sib_api_v3_sdk.rest import ApiException

def send_brevo_email(to_emails, subject, html_content, sender_email=None, sender_name=None, attachments=None):
    """
    Envía un correo usando la API de Brevo (Sendinblue) con soporte para adjuntos.
    """
    api_key = getattr(settings, "BREVO_API_KEY", None)
    if not api_key:
        raise ValueError("La variable BREVO_API_KEY no está configurada en settings.py")

    sender_email = sender_email or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@tu-dominio.com")
    sender_name = sender_name or "CineDot"

    configuration = Configuration()
    configuration.api_key["api-key"] = api_key

    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    # Formato de destinatarios
    to_list = [{"email": email} for email in to_emails]

    # Preparar adjuntos si existen
    attachment_list = []
    if attachments:
        for attachment in attachments:
            attachment_list.append(
                SendSmtpEmailAttachment(
                    name=attachment.get('name'),
                    content=attachment.get('content')
                )
            )

    send_smtp_email = SendSmtpEmail(
        to=to_list,
        sender={"email": sender_email, "name": sender_name},
        subject=subject,
        html_content=html_content,
        attachment=attachment_list if attachment_list else None
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        return True
    except ApiException as e:
        print(f"Error al enviar email con Brevo: {e}")
        raise