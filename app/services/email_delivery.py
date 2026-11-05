"""Send transactional email through Brevo HTTPS API or authenticated SMTP.

Configure secrets only in the environment. Tests capture emails in memory
instead of contacting real recipients. Never log full email bodies or keys.
"""
import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app


class EmailDeliveryError(RuntimeError):
    pass


def send_email(recipient, subject, body):
    app = current_app
    # Guard all tests against accidentally contacting live SMTP/API services.
    if app.testing:
        app.extensions.setdefault("edumind_test_outbox", []).append(
            {"to": recipient, "subject": subject, "body": body}
        )
        return

    sender = app.config.get("EMAIL_FROM", "").strip()
    if not sender:
        raise EmailDeliveryError("EMAIL_FROM must be configured.")

    backend = app.config.get("EMAIL_BACKEND", "smtp").strip().lower()
    if backend == "brevo":
        key = app.config.get("BREVO_API_KEY", "").strip()
        if not key:
            raise EmailDeliveryError("BREVO_API_KEY is not configured.")
        import httpx
        try:
            response = httpx.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": key, "accept": "application/json"},
                json={
                    "sender": {"email": sender, "name": "EduMind AI"},
                    "to": [{"email": recipient}],
                    "subject": subject,
                    "textContent": body,
                },
                timeout=12,
            )
            response.raise_for_status()
        except (httpx.HTTPError, ValueError) as exc:
            raise EmailDeliveryError("Email delivery service is unavailable.") from exc
        return

    if backend != "smtp":
        raise EmailDeliveryError("Unsupported EMAIL_BACKEND.")

    host = app.config.get("SMTP_HOST", "").strip()
    username = app.config.get("SMTP_USER", "").strip()
    password = app.config.get("SMTP_PASSWORD", "")
    port = int(app.config.get("SMTP_PORT", 587))
    use_ssl = bool(app.config.get("SMTP_USE_SSL", False))
    use_starttls = bool(app.config.get("SMTP_USE_STARTTLS", True))
    if not host or (username and not password):
        raise EmailDeliveryError("SMTP settings are incomplete.")
    if not use_ssl and not use_starttls and not app.config.get("EMAIL_ALLOW_INSECURE_SMTP", False):
        raise EmailDeliveryError("Encrypted SMTP transport is required.")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=12, context=context) as server:
                if username:
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=12) as server:
                server.ehlo()
                if use_starttls:
                    server.starttls(context=context)
                    server.ehlo()
                if username:
                    server.login(username, password)
                server.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Email delivery service is unavailable.") from exc
