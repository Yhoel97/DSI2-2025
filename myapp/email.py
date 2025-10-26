from django.conf import settings
import base64
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, SendSmtpEmail, TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException


def send_brevo_email(to_emails, subject, html_content, sender_email=None, sender_name=None, attachments=None):
    """
    Envía un correo usando la API de Brevo (Sendinblue).
    Ahora soporta adjuntos (ej: PDF de ticket).
    """
    api_key = getattr(settings, "BREVO_API_KEY", None)
    if not api_key:
        raise ValueError("La variable BREVO_API_KEY no está configurada en settings.py")

    sender_email = sender_email or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@tu-dominio.com")
    sender_name = sender_name or "Tu Aplicación"

    configuration = Configuration()
    configuration.api_key["api-key"] = api_key

    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    # Formato de destinatarios
    to_list = [{"email": email} for email in to_emails]

    # Construcción del objeto de correo
    send_smtp_email = SendSmtpEmail(
        to=to_list,
        sender={"email": sender_email, "name": sender_name},
        subject=subject,
        html_content=html_content,
    )

    # ✅ Adjuntar archivos si existen
    if attachments:
        # attachments debe ser una lista de tuplas: (filename, content_bytes, mimetype)
        send_smtp_email.attachment = []
        for filename, content, mimetype in attachments:
            # Brevo espera base64
            import base64
            encoded_content = base64.b64encode(content).decode("utf-8")
            send_smtp_email.attachment.append({
                "name": filename,
                "content": encoded_content
            })

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print(f"Error al enviar email con Brevo: {e}")
        raise