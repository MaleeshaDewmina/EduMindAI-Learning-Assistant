"""Read-only dashboard statistics derived from stored student activity.

Dates use UTC to match the application's existing UTC database timestamps.
These measurements are behavioural indicators, not validated motivation scores.
"""
from datetime import datetime, timedelta

from app.models.activity_log import UserActivityLog
from app.models.study_task import StudyTask


def build_chart_data(user_id, metrics, motivation, now=None):
    now = now or datetime.utcnow()
    first_day = now.date() - timedelta(days=6)
    start_dt = datetime.combine(first_day, datetime.min.time())
    days = [first_day + timedelta(days=offset) for offset in range(7)]
    labels = [day.strftime("%a %d") for day in days]

    completed_tasks = StudyTask.query.filter(
        StudyTask.user_id == user_id,
        StudyTask.status == "Completed",
        StudyTask.completed_at >= start_dt,
    ).all()
    activity_logs = UserActivityLog.query.filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.created_at >= start_dt,
    ).all()

    completed_by_day = {day: 0 for day in days}
    activity_by_day = {day: 0 for day in days}

    for task in completed_tasks:
        if task.completed_at and task.completed_at.date() in completed_by_day:
            completed_by_day[task.completed_at.date()] += 1
    for activity in activity_logs:
        if activity.created_at and activity.created_at.date() in activity_by_day:
            activity_by_day[activity.created_at.date()] += 1

    return {
        "status_labels": ["Completed", "Pending", "Overdue"],
        "status_values": [
            metrics["completed_tasks"], metrics["pending_tasks"], metrics["overdue_tasks"]
        ],
        "week_labels": labels,
        "weekly_completed": [completed_by_day[day] for day in days],
        "weekly_activity": [activity_by_day[day] for day in days],
        "score_labels": ["Task completion", "Recorded engagement", "Activity consistency"],
        "score_values": [
            float(motivation["task_completion_score"]),
            float(motivation["engagement_score"]),
            float(motivation["consistency_score"]),
        ],
    }


def build_dashboard_insight(metrics):
    total = metrics["total_tasks"]
    pending = metrics["pending_tasks"]
    overdue = metrics["overdue_tasks"]
    completed = metrics["completed_tasks"]

    if total == 0:
        return (
            "Create a study task to begin tracking your progress. "
            "Your dashboard will use recorded tasks and activity to provide feedback."
        )
    if overdue:
        return (
            f"You have {overdue} overdue task(s). Review the nearest deadline "
            "and break the work into manageable steps."
        )
    if pending == 0 and completed == total:
        return (
            "All your current study tasks are complete. Well done for following through! "
            "Consider adding a new achievable goal and reviewing what helped."
        )
    if pending > 0:
        return (
            f"You have {pending} pending task(s). Choose one manageable next step "
            "and build on your progress at a sustainable pace."
        )
    return (
        "Keep reviewing your study plan and learning activity. "
        "Small, consistent actions can support your progress."
    )
