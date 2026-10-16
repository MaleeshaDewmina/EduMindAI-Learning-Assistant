from datetime import datetime
from app.extensions import db


class UserActivityLog(db.Model):
    __tablename__ = "user_activity_logs"

    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    activity_name = db.Column(db.String(100), nullable=False)
    activity_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="activity_logs")