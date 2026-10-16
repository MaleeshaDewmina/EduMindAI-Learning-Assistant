from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services.analytics_service import (
    get_task_metrics,
    calculate_motivation_score,
    get_recent_activity_logs,
)
from app.services.dashboard_service import build_chart_data, build_dashboard_insight


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    metrics = get_task_metrics(current_user.user_id)
    motivation = calculate_motivation_score(current_user.user_id)
    recent_activities = get_recent_activity_logs(current_user.user_id, limit=5)
    charts = build_chart_data(current_user.user_id, metrics, motivation)
    insight = build_dashboard_insight(metrics)

    return render_template(
        "dashboard/index.html",
        user=current_user,
        total_tasks=metrics["total_tasks"],
        completed_tasks=metrics["completed_tasks"],
        pending_tasks=metrics["pending_tasks"],
        overdue_tasks=metrics["overdue_tasks"],
        completion_rate=metrics["completion_rate"],
        motivation_score=motivation["overall_motivation_score"],
        engagement_score=motivation["engagement_score"],
        consistency_score=motivation["consistency_score"],
        chart_data=charts,
        insight=insight,
        recent_activities=recent_activities,
    )
