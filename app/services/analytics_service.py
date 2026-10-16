from datetime import datetime, timedelta
from sqlalchemy import func

from app.extensions import db
from app.models.study_task import StudyTask
from app.models.progress_log import ProgressLog
from app.models.activity_log import UserActivityLog
from app.models.motivation_score import MotivationScore


def update_overdue_tasks_for_user(user_id):
    now = datetime.utcnow()

    overdue_tasks = StudyTask.query.filter(
        StudyTask.user_id == user_id,
        StudyTask.status == "Pending",
        StudyTask.deadline < now
    ).all()

    for task in overdue_tasks:
        task.status = "Overdue"

    if overdue_tasks:
        db.session.commit()


def get_task_metrics(user_id):
    update_overdue_tasks_for_user(user_id)

    total_tasks = StudyTask.query.filter_by(user_id=user_id).count()
    completed_tasks = StudyTask.query.filter_by(user_id=user_id, status="Completed").count()
    pending_tasks = StudyTask.query.filter_by(user_id=user_id, status="Pending").count()
    overdue_tasks = StudyTask.query.filter_by(user_id=user_id, status="Overdue").count()

    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 2)
    else:
        completion_rate = 0.00

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": completion_rate
    }


def log_activity(user_id, activity_name, activity_details=None):
    activity = UserActivityLog(
        user_id=user_id,
        activity_name=activity_name,
        activity_details=activity_details
    )

    db.session.add(activity)
    db.session.commit()


def log_progress(user_id, activity_type, task_id=None):
    metrics = get_task_metrics(user_id)

    progress_log = ProgressLog(
        user_id=user_id,
        task_id=task_id,
        activity_type=activity_type,
        completion_rate=metrics["completion_rate"]
    )

    db.session.add(progress_log)
    db.session.commit()


def calculate_engagement_score(user_id):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    activity_count = UserActivityLog.query.filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.created_at >= seven_days_ago
    ).count()

    score = min(activity_count * 10, 100)

    return round(score, 2)


def calculate_consistency_score(user_id):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    active_days = db.session.query(
        func.date(UserActivityLog.created_at)
    ).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.created_at >= seven_days_ago
    ).distinct().count()

    score = min((active_days / 7) * 100, 100)

    return round(score, 2)


def calculate_motivation_score(user_id):
    metrics = get_task_metrics(user_id)

    task_completion_score = metrics["completion_rate"]
    engagement_score = calculate_engagement_score(user_id)
    consistency_score = calculate_consistency_score(user_id)

    overall_score = round(
        (task_completion_score * 0.50) +
        (engagement_score * 0.25) +
        (consistency_score * 0.25),
        2
    )

    motivation_score = MotivationScore(
        user_id=user_id,
        task_completion_score=task_completion_score,
        engagement_score=engagement_score,
        consistency_score=consistency_score,
        overall_motivation_score=overall_score
    )

    db.session.add(motivation_score)
    db.session.commit()

    return {
        "task_completion_score": task_completion_score,
        "engagement_score": engagement_score,
        "consistency_score": consistency_score,
        "overall_motivation_score": overall_score
    }


def get_recent_progress_logs(user_id, limit=8):
    return ProgressLog.query.filter_by(
        user_id=user_id
    ).order_by(
        ProgressLog.log_date.desc()
    ).limit(limit).all()


def get_recent_activity_logs(user_id, limit=8):
    return UserActivityLog.query.filter_by(
        user_id=user_id
    ).order_by(
        UserActivityLog.created_at.desc()
    ).limit(limit).all()