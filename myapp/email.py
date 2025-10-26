import base64
import logging
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, SendSmtpEmail, TransactionalEmailsApi, SendSmtpEmailAttachment
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)

def enviar_ticket_por_correo(reserva, pdf_buffer, email_cliente):
    """
    Envía el ticket PDF por correo usando Brevo (Sendinblue).
    """
    try:
        # Convertir PDF a base64
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()

        # Configuración de Brevo
        api_key = getattr(settings, "BREVO_API_KEY", None)
        if not api_key:
            logger.error("BREVO_API_KEY no está configurada en settings.py")
            return False

        configuration = Configuration()
        configuration.api_key["api-key"] = api_key
        api_client = ApiClient(configuration)
        api_instance = TransactionalEmailsApi(api_client)

        # Crear adjunto
        attachment = SendSmtpEmailAttachment(
            name=f"ticket_{reserva.codigo_reserva}.pdf",
            content=pdf_base64,
            content_type="application/pdf"
        )

        # Crear email
        send_smtp_email = SendSmtpEmail(
            to=[{"email": email_cliente}],
            sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "CineDot"},
            subject=f"Tu ticket para {reserva.pelicula.nombre} - CineDot",
            html_content="""
                <html>
                <body>
                    <p>Aquí está tu ticket.</p>
                    <p>Gracias por preferir a CineDot.</p>
                </body>
                </html>
            """,
            attachment=[attachment]
        )

        # Enviar correo
        response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Ticket enviado exitosamente a {email_cliente}. Respuesta: {response}")
        return True

    except ApiException as e:
        logger.error(f"Error API Brevo: {e}")
        logger.error(f"Respuesta completa: {e.body}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar ticket: {str(e)}")
        return False