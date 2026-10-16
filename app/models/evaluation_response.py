from datetime import datetime
from app.extensions import db


class EvaluationResponse(db.Model):
    __tablename__ = "evaluation_responses"

    response_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    evaluation_type = db.Column(db.String(20), nullable=False)
    motivation_rating = db.Column(db.Integer, nullable=False)
    confidence_rating = db.Column(db.Integer, nullable=False)
    growth_mindset_rating = db.Column(db.Integer, nullable=False)
    usability_rating = db.Column(db.Integer, nullable=False)

    feedback_comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="evaluation_responses")