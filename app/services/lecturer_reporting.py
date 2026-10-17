"""Read-only consent-scoped reporting; never writes MotivationScore history."""
from datetime import datetime, timedelta
from sqlalchemy import func

from app.extensions import db
from app.models.study_task import StudyTask
from app.models.activity_log import UserActivityLog
from app.routes.evaluation_routes import current_version_response, comparison


def report_for_student(student_id, now=None):
    now = now or datetime.utcnow()
    tasks = StudyTask.query.filter_by(user_id=student_id).all()
    completed = sum(t.status == "Completed" for t in tasks)
    overdue = sum(t.status != "Completed" and (t.status == "Overdue" or t.deadline < now) for t in tasks)
    pending = len(tasks) - completed - overdue
    completion = round(100.0 * completed / len(tasks), 2) if tasks else 0.0

    week_ago = now - timedelta(days=7)
    recent = UserActivityLog.query.filter(
        UserActivityLog.user_id == student_id,
        UserActivityLog.created_at >= week_ago,
        UserActivityLog.created_at <= now,
    )
    activity_events = recent.count()
    active_days = db.session.query(func.date(UserActivityLog.created_at)).filter(
        UserActivityLog.user_id == student_id,
        UserActivityLog.created_at >= week_ago,
        UserActivityLog.created_at <= now,
    ).distinct().count()
    engagement = min(activity_events * 10, 100)
    consistency = round(min(active_days / 7 * 100, 100), 2)
    indicator = round(completion * 0.5 + engagement * 0.25 + consistency * 0.25, 2)

    pre = current_version_response(student_id, "PreTest")
    post = current_version_response(student_id, "PostTest")
    return {
        "total": len(tasks), "completed": completed, "pending": pending,
        "overdue": overdue, "completion": completion,
        "activity_events": activity_events, "active_days": active_days,
        "engagement": engagement, "consistency": consistency,
        "indicator": indicator, "evaluation": comparison(pre, post),
        "has_pre": pre is not None, "has_post": post is not None,
    }
