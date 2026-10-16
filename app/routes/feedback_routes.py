from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db

from app.services.analytics_service import get_task_metrics, calculate_motivation_score, log_activity
from app.services.feedback_service import (
    create_personalized_feedback,
    get_latest_feedback,
    get_feedback_history
)


feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback_bp.route("/")
@login_required
def index():
    metrics = get_task_metrics(current_user.user_id)
    motivation = calculate_motivation_score(current_user.user_id)
    latest_feedback = get_latest_feedback(current_user.user_id)
    feedback_history = get_feedback_history(current_user.user_id)

    return render_template(
        "feedback/index.html",
        metrics=metrics,
        motivation=motivation,
        latest_feedback=latest_feedback,
        feedback_history=feedback_history
    )


@feedback_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    try:
        feedback = create_personalized_feedback(current_user.user_id)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not save personalised feedback")
        flash("Feedback could not be saved. Please check the database schema.", "danger")
        return redirect(url_for("feedback.index"))

    log_activity(
        current_user.user_id,
        "Feedback Generated",
        f"Generated personalized {feedback.feedback_type} feedback."
    )

    flash("Personalized feedback generated successfully.", "success")
    return redirect(url_for("feedback.index"))