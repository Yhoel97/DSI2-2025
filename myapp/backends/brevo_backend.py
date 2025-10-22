from django.core.mail.backends.base import BaseEmailBackend
from myapp.email import send_brevo_email


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        num_sent = 0
        for message in email_messages:
            try:
                # Obtener el contenido adecuado
                if hasattr(message, "alternatives") and message.alternatives:
                    # Si tiene versión HTML
                    html_content = message.alternatives[0][0]
                else:
                    # Si solo tiene texto plano
                    html_content = f"<pre>{message.body}</pre>"

                send_brevo_email(
                    [addr for addr in message.to],
                    message.subject,
                    html_content,
                )
                num_sent += 1
            except Exception as e:
                print(f"❌ Error enviando correo con Brevo: {e}")
                if not self.fail_silently:
                    raise
        return num_sent
