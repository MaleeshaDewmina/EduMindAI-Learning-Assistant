"""Database-backed throttling of failed login attempts.

The existing email_action_events table is used for privacy-preserving,
cross-worker rate limiting. Email addresses are stored only as keyed digests.
Do not use a process-local counter on multi-worker WSGI hosting.
"""
from datetime import datetime, timedelta
import hashlib
import hmac

from flask import current_app, request
from app.extensions import db
from app.models.email_action_event import EmailActionEvent

LOGIN_FAILURE_WINDOW = timedelta(minutes=15)
LOGIN_FAILURE_LIMIT = 8


def _login_address_digest(email):
    normalized = (email or "").strip().lower()
    return hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def too_many_login_failures(email):
    """All addresses, whether registered or not, use the same limit."""
    since = datetime.utcnow() - LOGIN_FAILURE_WINDOW
    return (
        EmailActionEvent.query.filter_by(
            purpose="login_failure", address_digest=_login_address_digest(email)
        )
        .filter(EmailActionEvent.created_at >= since)
        .count()
        >= LOGIN_FAILURE_LIMIT
    )


def record_failed_login(email):
    """Persist one unsuccessful attempt without storing credentials or raw IPs."""
    # The IP is deliberately not used as a hard blocker: a shared campus
    # or alwaysdata reverse-proxy address could lock out unrelated users.
    digest = _login_address_digest(email)
    db.session.add(
        EmailActionEvent(
            purpose="login_failure",
            user_id=None,
            address_digest=digest,
            ip_digest=_login_address_digest("ip:" + (request.remote_addr or "unknown")),
            created_at=datetime.utcnow(),
        )
    )
    db.session.commit()
