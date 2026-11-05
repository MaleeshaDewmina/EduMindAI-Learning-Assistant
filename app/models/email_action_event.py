"""Persisted reset-token and report-send audit events; no plaintext tokens or messages."""
from datetime import datetime
from app.extensions import db


class EmailActionEvent(db.Model):
    __tablename__ = "email_action_events"

    event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    purpose = db.Column(db.String(32), nullable=False, index=True)
    address_digest = db.Column(db.String(64), nullable=False, index=True)
    ip_digest = db.Column(db.String(64), nullable=False, index=True)
    token_digest = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    consumed_at = db.Column(db.DateTime, nullable=True)
