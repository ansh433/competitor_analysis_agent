import smtplib
from email.message import EmailMessage

from app.core.config import Settings


def send_password_reset_email(recipient: str, reset_url: str, settings: Settings) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        return

    message = EmailMessage()
    message["Subject"] = "Reset your Compass Intelligence password"
    message["From"] = str(settings.smtp_from_email)
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your account. "
        f"Use this one-time link before it expires: {reset_url}"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password.get_secret_value())
        smtp.send_message(message)
