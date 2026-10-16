from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.evaluation_response import EvaluationResponse
from app.services.analytics_service import log_activity


evaluation_bp = Blueprint("evaluation", __name__, url_prefix="/evaluation")


@evaluation_bp.route("/")
@login_required
def index():
    responses = EvaluationResponse.query.filter_by(
        user_id=current_user.user_id
    ).order_by(
        EvaluationResponse.submitted_at.desc()
    ).all()

    pre_test = EvaluationResponse.query.filter_by(
        user_id=current_user.user_id,
        evaluation_type="PreTest"
    ).order_by(
        EvaluationResponse.submitted_at.desc()
    ).first()

    post_test = EvaluationResponse.query.filter_by(
        user_id=current_user.user_id,
        evaluation_type="PostTest"
    ).order_by(
        EvaluationResponse.submitted_at.desc()
    ).first()

    summary = get_user_evaluation_summary(current_user.user_id)

    return render_template(
        "evaluation/index.html",
        responses=responses,
        pre_test=pre_test,
        post_test=post_test,
        summary=summary
    )


@evaluation_bp.route("/pre-test", methods=["GET", "POST"])
@login_required
def pre_test():
    return handle_evaluation_form("PreTest")


@evaluation_bp.route("/post-test", methods=["GET", "POST"])
@login_required
def post_test():
    return handle_evaluation_form("PostTest")


def handle_evaluation_form(evaluation_type):
    if request.method == "POST":
        try:
            motivation_rating = int(request.form.get("motivation_rating"))
            confidence_rating = int(request.form.get("confidence_rating"))
            growth_mindset_rating = int(request.form.get("growth_mindset_rating"))
            usability_rating = int(request.form.get("usability_rating"))
        except (TypeError, ValueError):
            flash("Please select all rating values.", "danger")
            return redirect(request.url)

        feedback_comments = request.form.get("feedback_comments", "").strip()

        if not all(1 <= value <= 5 for value in [
            motivation_rating,
            confidence_rating,
            growth_mindset_rating,
            usability_rating
        ]):
            flash("Ratings must be between 1 and 5.", "danger")
            return redirect(request.url)

        response = EvaluationResponse(
            user_id=current_user.user_id,
            evaluation_type=evaluation_type,
            motivation_rating=motivation_rating,
            confidence_rating=confidence_rating,
            growth_mindset_rating=growth_mindset_rating,
            usability_rating=usability_rating,
            feedback_comments=feedback_comments if feedback_comments else None
        )

        db.session.add(response)
        db.session.commit()

        log_activity(
            current_user.user_id,
            "Evaluation Submitted",
            f"Submitted {evaluation_type} questionnaire."
        )

        flash(f"{evaluation_type} questionnaire submitted successfully.", "success")
        return redirect(url_for("evaluation.index"))

    return render_template(
        "evaluation/form.html",
        evaluation_type=evaluation_type
    )


def get_user_evaluation_summary(user_id):
    result = db.session.query(
        func.avg(EvaluationResponse.motivation_rating),
        func.avg(EvaluationResponse.confidence_rating),
        func.avg(EvaluationResponse.growth_mindset_rating),
        func.avg(EvaluationResponse.usability_rating)
    ).filter(
        EvaluationResponse.user_id == user_id
    ).first()

    return {
        "motivation_avg": round(float(result[0]), 2) if result[0] else 0,
        "confidence_avg": round(float(result[1]), 2) if result[1] else 0,
        "growth_mindset_avg": round(float(result[2]), 2) if result[2] else 0,
        "usability_avg": round(float(result[3]), 2) if result[3] else 0
    }