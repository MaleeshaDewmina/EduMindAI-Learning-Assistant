from app.extensions import db
from app.models.feedback import Feedback
from app.services.analytics_service import get_task_metrics, calculate_motivation_score
from app.services.recommendation_service import generate_recommendation


def create_personalized_feedback(user_id):
    metrics = get_task_metrics(user_id)
    motivation = calculate_motivation_score(user_id)

    result = generate_recommendation(metrics, motivation)

    feedback = Feedback(
        user_id=user_id,
        feedback_message=result["message"],
        feedback_type=result["feedback_type"],
        recommendation=result["recommendation"]
    )

    db.session.add(feedback)
    db.session.commit()

    return feedback


def get_latest_feedback(user_id):
    return Feedback.query.filter_by(
        user_id=user_id
    ).order_by(
        Feedback.created_at.desc()
    ).first()


def get_feedback_history(user_id, limit=8):
    return Feedback.query.filter_by(
        user_id=user_id
    ).order_by(
        Feedback.created_at.desc()
    ).limit(limit).all()