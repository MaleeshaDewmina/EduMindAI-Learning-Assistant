"""Student-owned study task CRUD and progress event recording.

Tasks use the project's existing naive UTC database timestamps. The browser's
`datetime-local` input has no timezone: the stored deadline follows the
application's existing convention. Future work can expose user time zones.
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.progress_log import ProgressLog
from app.models.study_task import StudyTask
from app.services.analytics_service import (
    log_activity,
    log_progress,
    update_overdue_tasks_for_user,
)

planner_bp = Blueprint("planner", __name__, url_prefix="/planner")
VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_EDIT_STATUSES = {"Pending", "Completed"}


def _validated_task_fields(form):
    """Return (fields, error_message); validate on server, not just HTML."""
    title = form.get("title", "").strip()
    subject = form.get("subject", "").strip()
    description = form.get("description", "").strip()
    priority = form.get("priority", "Medium")
    deadline_value = form.get("deadline", "").strip()

    if not 1 <= len(title) <= 150:
        return None, "Task title must contain 1 to 150 characters."
    if len(subject) > 100:
        return None, "Subject must not exceed 100 characters."
    if len(description) > 3000:
        return None, "Description must not exceed 3000 characters."
    if priority not in VALID_PRIORITIES:
        return None, "Select a valid task priority."
    try:
        deadline = datetime.strptime(deadline_value, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        return None, "Enter a valid deadline and time."

    return {
        "title": title,
        "subject": subject or None,
        "description": description or None,
        "priority": priority,
        "deadline": deadline,
    }, None


def _status_for_deadline(deadline):
    return "Overdue" if deadline < datetime.utcnow() else "Pending"


@planner_bp.route("/")
@login_required
def index():
    update_overdue_tasks_for_user(current_user.user_id)
    tasks = (
        StudyTask.query.filter_by(user_id=current_user.user_id)
        .order_by(StudyTask.deadline.asc())
        .all()
    )
    return render_template("planner/index.html", tasks=tasks)


@planner_bp.route("/create", methods=["POST"])
@login_required
def create():
    fields, error = _validated_task_fields(request.form)
    if error:
        flash(error, "danger")
        return redirect(url_for("planner.index"))

    new_task = StudyTask(
        user_id=current_user.user_id,
        status=_status_for_deadline(fields["deadline"]),
        **fields,
    )
    db.session.add(new_task)
    db.session.commit()

    log_activity(current_user.user_id, "Task Created", f"Created study task: {new_task.title}")
    log_progress(current_user.user_id, "Task Created", new_task.task_id)
    flash("Study task created successfully.", "success")
    return redirect(url_for("planner.index"))


@planner_bp.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = StudyTask.query.filter_by(
        task_id=task_id, user_id=current_user.user_id
    ).first_or_404()

    if request.method == "POST":
        fields, error = _validated_task_fields(request.form)
        if error:
            flash(error, "danger")
            return redirect(url_for("planner.edit", task_id=task.task_id))

        requested_status = request.form.get("status", "Pending")
        if requested_status not in VALID_EDIT_STATUSES:
            flash("Choose Pending or Completed. Overdue status is calculated from the deadline.", "danger")
            return redirect(url_for("planner.edit", task_id=task.task_id))

        old_status = task.status
        for key, value in fields.items():
            setattr(task, key, value)

        if requested_status == "Completed":
            task.status = "Completed"
            if old_status != "Completed" or task.completed_at is None:
                task.completed_at = datetime.utcnow()
        else:
            task.status = _status_for_deadline(task.deadline)
            task.completed_at = None

        db.session.commit()
        log_activity(current_user.user_id, "Task Updated", f"Updated study task: {task.title}")
        activity_type = (
            f"Task Status Changed from {old_status} to {task.status}"
            if old_status != task.status else "Task Updated"
        )
        log_progress(current_user.user_id, activity_type, task.task_id)
        flash("Study task updated successfully.", "success")
        return redirect(url_for("planner.index"))

    return render_template("planner/edit.html", task=task)


@planner_bp.route("/complete/<int:task_id>", methods=["POST"])
@login_required
def complete(task_id):
    task = StudyTask.query.filter_by(
        task_id=task_id, user_id=current_user.user_id
    ).first_or_404()

    if task.status == "Completed":
        flash("This task was already completed.", "info")
        return redirect(url_for("planner.index"))

    task.status = "Completed"
    task.completed_at = datetime.utcnow()
    db.session.commit()
    log_activity(current_user.user_id, "Task Completed", f"Completed study task: {task.title}")
    log_progress(current_user.user_id, "Task Completed", task.task_id)
    flash("Task marked as completed.", "success")
    return redirect(url_for("planner.index"))


@planner_bp.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    task = StudyTask.query.filter_by(
        task_id=task_id, user_id=current_user.user_id
    ).first_or_404()
    title = task.title

    # Preserve historical progress entries, while removing the task FK before deletion.
    ProgressLog.query.filter_by(task_id=task.task_id, user_id=current_user.user_id).update(
        {ProgressLog.task_id: None}, synchronize_session=False
    )
    db.session.delete(task)
    db.session.commit()
    log_activity(current_user.user_id, "Task Deleted", f"Deleted study task: {title}")
    log_progress(current_user.user_id, "Task Deleted", None)
    flash("Task deleted successfully.", "info")
    return redirect(url_for("planner.index"))
