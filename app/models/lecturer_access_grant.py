"""Student-controlled, revocable permissions for lecturer progress reports."""
from datetime import datetime
from app.extensions import db


class LecturerAccessGrant(db.Model):
    __tablename__ = "lecturer_access_grants"

    grant_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    granted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Email reports require separate, explicit student consent; default OFF.
    email_allowed = db.Column(db.Boolean, nullable=False, default=False, server_default='0')

    student = db.relationship("User", foreign_keys=[student_id])
    lecturer = db.relationship("User", foreign_keys=[lecturer_id])
    __table_args__ = (
        db.UniqueConstraint("student_id", "lecturer_id", name="uq_student_lecturer_grant"),
        db.CheckConstraint("student_id <> lecturer_id", name="ck_lecturer_grant_not_self"),
    )
