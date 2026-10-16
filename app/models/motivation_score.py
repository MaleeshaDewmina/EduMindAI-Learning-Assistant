from datetime import datetime
from app.extensions import db


class MotivationScore(db.Model):
    __tablename__ = "motivation_scores"

    score_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    task_completion_score = db.Column(db.Numeric(5, 2), default=0.00)
    engagement_score = db.Column(db.Numeric(5, 2), default=0.00)
    consistency_score = db.Column(db.Numeric(5, 2), default=0.00)
    overall_motivation_score = db.Column(db.Numeric(5, 2), default=0.00)

    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="motivation_scores")