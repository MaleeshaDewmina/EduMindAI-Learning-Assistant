from datetime import datetime
from app.extensions import db


class ProgressLog(db.Model):
    __tablename__ = "progress_logs"

    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("study_tasks.task_id"), nullable=True)

    activity_type = db.Column(db.String(100), nullable=False)
    completion_rate = db.Column(db.Numeric(5, 2), default=0.00)
    log_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="progress_logs")
    task = db.relationship("StudyTask", backref="progress_logs")