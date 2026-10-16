import json
import re
from datetime import datetime, timedelta

from app.extensions import db
from app.models.user import User
from app.models.study_task import StudyTask
from app.models.activity_log import UserActivityLog
from app.services.dashboard_service import build_chart_data, build_dashboard_insight
from werkzeug.security import generate_password_hash


def create_user(email):
    user = User(full_name="Chart Test", email=email, password_hash=generate_password_hash("SomeTestPassword123"))
    db.session.add(user)
    db.session.commit()
    return user


def metrics(total, completed, pending, overdue):
    return {
        "total_tasks": total, "completed_tasks": completed,
        "pending_tasks": pending, "overdue_tasks": overdue,
        "completion_rate": round(completed / total * 100, 2) if total else 0.0,
    }


def scores():
    return {"task_completion_score": 50, "engagement_score": 20, "consistency_score": 10}


def test_weekly_charts_use_only_current_students_data(app):
    with app.app_context():
        user = create_user("charts1@example.org")
        other = create_user("charts2@example.org")
        now = datetime.utcnow()
        db.session.add_all([
            StudyTask(user_id=user.user_id, title="Finished", deadline=now + timedelta(days=2), status="Completed", completed_at=now),
            StudyTask(user_id=other.user_id, title="Someone else's task", deadline=now + timedelta(days=2), status="Completed", completed_at=now),
            UserActivityLog(user_id=user.user_id, activity_name="Task Completed", created_at=now),
            UserActivityLog(user_id=other.user_id, activity_name="Task Completed", created_at=now),
        ])
        db.session.commit()
        data = build_chart_data(user.user_id, metrics(1,1,0,0), scores(), now=now)
        assert data["status_values"] == [1,0,0]
        assert len(data["week_labels"]) == 7
        assert sum(data["weekly_completed"]) == 1
        assert sum(data["weekly_activity"]) == 1
        assert data["score_values"] == [50.0,20.0,10.0]


def test_old_activity_excluded_from_last_seven_calendar_days(app):
    with app.app_context():
        user = create_user("dates@example.org")
        now = datetime.utcnow()
        db.session.add(UserActivityLog(user_id=user.user_id, activity_name="Old", created_at=now - timedelta(days=12)))
        db.session.commit()
        data = build_chart_data(user.user_id, metrics(0,0,0,0), scores(), now=now)
        assert sum(data["weekly_activity"]) == 0


def test_dashboard_insight_does_not_suggest_nonexistent_pending_tasks():
    msg = build_dashboard_insight(metrics(1,1,0,0)).lower()
    assert "complete" in msg
    assert "pending" not in msg
    assert "overdue" in build_dashboard_insight(metrics(2,0,1,1)).lower()
    assert "create" in build_dashboard_insight(metrics(0,0,0,0)).lower()


def test_dashboard_page_includes_real_charts_and_favicon(client, app):
    # Uses the same in-memory SQLite test fixture as Phase 1.
    from tests.test_auth_security import register, login
    register(client, email="dash@example.org")
    login(client, email="dash@example.org")
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert b"Learning Analytics" in response.data
    assert b"not a validated psychological measure" in response.data
    assert b"dashboard-chart-data" in response.data
    assert client.get("/static/images/favicon.svg").status_code == 200
