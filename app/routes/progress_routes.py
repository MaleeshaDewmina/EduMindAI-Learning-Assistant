from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services.analytics_service import (
    get_task_metrics,
    calculate_motivation_score,
    get_recent_progress_logs,
    get_recent_activity_logs
)


progress_bp = Blueprint("progress", __name__, url_prefix="/progress")


@progress_bp.route("/")
@login_required
def index():
    metrics = get_task_metrics(current_user.user_id)
    motivation = calculate_motivation_score(current_user.user_id)
    progress_logs = get_recent_progress_logs(current_user.user_id, limit=10)
    activity_logs = get_recent_activity_logs(current_user.user_id, limit=10)

    return render_template(
        "progress/index.html",
        metrics=metrics,
        motivation=motivation,
        progress_logs=progress_logs,
        activity_logs=activity_logs
    )