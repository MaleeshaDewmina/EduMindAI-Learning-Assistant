from datetime import datetime
from app.extensions import db


class StudyTask(db.Model):
    __tablename__ = "study_tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(100), nullable=True)

    priority = db.Column(db.String(20), default="Medium")
    status = db.Column(db.String(20), default="Pending")

    deadline = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="study_tasks")