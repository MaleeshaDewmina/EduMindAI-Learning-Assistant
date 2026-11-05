"""Privacy-scoped, rate-limited actions for password recovery and progress emails."""
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets

from flask import current_app, request
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.email_action_event import EmailActionEvent
from app.models.user import User
from app.services.email_delivery import send_email


def _digest(value):
    return hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _ip_digest():
    # Do not trust user-supplied X-Forwarded-For unless ProxyFix is explicitly configured.
    return _digest(request.remote_addr or "unknown")


def _address_digest(email):
    return _digest(email.strip().lower())


def _recent_count(purpose, since, **filters):
    return EmailActionEvent.query.filter_by(purpose=purpose, **filters).filter(
        EmailActionEvent.created_at >= since
    ).count()


def request_password_reset(email, invitation=False):
    """Non-enumerating reset: 3/hour per address and 30/hour per remote IP.

    Both known and unknown addresses are logged as digests only; never store
    plaintext reset tokens. Return the same generic browser message.
    """
    now = datetime.utcnow()
    email = (email or "").strip().lower()
    address_hash = _address_digest(email)
    ip_hash = _ip_digest()
    hour = now - timedelta(hours=1)
    if _recent_count("reset", hour, address_digest=address_hash) >= 3:
        return
    if _recent_count("reset", hour, ip_digest=ip_hash) >= 30:
        return

    user = User.query.filter_by(email=email, is_active=True).first()
    token = secrets.token_urlsafe(32) if user is not None else None
    event = EmailActionEvent(
        user_id=user.user_id if user else None,
        purpose="reset",
        address_digest=address_hash,
        ip_digest=ip_hash,
        token_digest=hashlib.sha256(token.encode("utf-8")).hexdigest() if token else None,
        created_at=now,
        expires_at=now + timedelta(minutes=30) if token else None,
    )
    db.session.add(event)
    db.session.commit()

    if not user:
        return
    public_base = (current_app.config.get("APP_PUBLIC_URL") or "").rstrip("/")
    if not public_base:
        if current_app.testing:
            public_base = "http://localhost"
        else:
            current_app.logger.error("Cannot send reset link: APP_PUBLIC_URL is unset.")
            return
    if not (public_base.startswith("https://") or (
        current_app.testing and public_base.startswith("http://")
    )):
        current_app.logger.error("APP_PUBLIC_URL must be HTTPS on live hosting.")
        return

    link = f"{public_base}/auth/reset-password/{token}"
    if invitation:
        subject = "Set up your EduMind AI staff account"
        text = (
            "An EduMind AI administrator created a staff account for this email address.\\n\\n"
            f"Set your password within 30 minutes:\\n{link}\\n\\n"
            "If you did not expect this invitation, ignore it and contact the system administrator. "
            "This link works once only.\\n"
        )
    else:
        subject = "Reset your EduMind AI password"
        text = (
            "A password reset was requested for your EduMind AI account.\\n\\n"
            f"Open this link within 30 minutes:\\n{link}\\n\\n"
            "If you did not request this reset, ignore the email. "
            "The link works once only.\\n"
        )
    send_email(user.email, subject, text)


def check_reset_token(token):
    if not token or len(token) > 128:
        return None
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    event = EmailActionEvent.query.filter_by(
        purpose="reset", token_digest=digest, consumed_at=None
    ).first()
    if not event or not event.expires_at or event.expires_at <= datetime.utcnow():
        return None
    user = db.session.get(User, event.user_id) if event.user_id is not None else None
    return (event, user) if user and user.is_active else None


def use_reset_token(token, password):
    found = check_reset_token(token)
    if not found:
        return False
    event, user = found
    now = datetime.utcnow()
    # Conditional UPDATE avoids using an already consumed token if requests race.
    updated = EmailActionEvent.query.filter(
        EmailActionEvent.event_id == event.event_id,
        EmailActionEvent.consumed_at.is_(None),
        EmailActionEvent.expires_at > now,
    ).update({"consumed_at": now}, synchronize_session=False)
    if updated != 1:
        db.session.rollback()
        return False
    user.password_hash = generate_password_hash(password)
    # All earlier reset links for this user are invalidated.
    EmailActionEvent.query.filter(
        EmailActionEvent.purpose == "reset",
        EmailActionEvent.user_id == user.user_id,
        EmailActionEvent.consumed_at.is_(None),
    ).update({"consumed_at": now}, synchronize_session=False)
    db.session.commit()
    return True


def allow_report_send(user, purpose):
    now = datetime.utcnow()
    hour = now - timedelta(hours=1)
    ip_hash = _ip_digest()
    address_hash = _address_digest(user.email)
    if _recent_count(purpose, hour, user_id=user.user_id) >= 3:
        return False
    if _recent_count(purpose, hour, ip_digest=ip_hash) >= 30:
        return False
    event = EmailActionEvent(
        user_id=user.user_id, purpose=purpose,
        address_digest=address_hash, ip_digest=ip_hash, created_at=now,
    )
    db.session.add(event)
    db.session.commit()
    return True


def report_email_body(student, report, recipient_role):
    name = student.full_name if recipient_role == "lecturer" else "you"
    return (
        f"EduMind AI Progress Report\n"
        f"Student: {name}\n"
        f"Tasks: {report['total']} total, {report['completed']} completed, "
        f"{report['pending']} pending, {report['overdue']} overdue\n"
        f"Completion rate: {report['completion']:.1f}%\n"
        f"Activity events (last 7 days): {report['activity_events']}\n"
        f"Active days (last 7 days): {report['active_days']} of 7\n"
        f"Behavioural indicator: {report['indicator']:.1f}%\n\n"
        "This indicator represents recorded application activity, not a validated "
        "psychological measure. No chat history, uploaded documents, questionnaire "
        "comments or individual item responses are included.\n"
    )
