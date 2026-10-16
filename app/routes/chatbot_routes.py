from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models.chat_message import ChatMessage
from app.services.groq_service import generate_ai_response, AIServiceError
from app.services.analytics_service import get_task_metrics, log_activity


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")
MAX_CHAT_MESSAGE_LENGTH = 2000


def classify_message_type(message):
    text = message.lower()

    if any(word in text for word in ["motivate", "stress", "tired", "lazy", "focus", "confidence"]):
        return "Motivational"

    if any(word in text for word in ["plan", "schedule", "deadline", "task", "study plan"]):
        return "StudyPlanning"

    if any(word in text for word in ["explain", "what is", "how to", "assignment", "exam"]):
        return "Academic"

    return "General"


@chatbot_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        user_message = request.form.get("message", "").strip()

        if not user_message:
            flash("Please type a message before sending.", "danger")
            return redirect(url_for("chatbot.index"))

        if len(user_message) > MAX_CHAT_MESSAGE_LENGTH:
            flash(f"Please keep your message within {MAX_CHAT_MESSAGE_LENGTH} characters.", "danger")
            return redirect(url_for("chatbot.index"))

        metrics = get_task_metrics(current_user.user_id)

        # Send only task metrics; personal identifiers are unnecessary for study support.
        student_context = f"""
Total study tasks: {metrics["total_tasks"]}
Completed tasks: {metrics["completed_tasks"]}
Pending tasks: {metrics["pending_tasks"]}
Overdue tasks: {metrics["overdue_tasks"]}
Task completion rate: {metrics["completion_rate"]}%
"""

        try:
            ai_response = generate_ai_response(user_message, student_context)
        except AIServiceError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("chatbot.index"))

        message_type = classify_message_type(user_message)

        chat = ChatMessage(
            user_id=current_user.user_id,
            user_message=user_message,
            ai_response=ai_response,
            message_type=message_type
        )

        db.session.add(chat)
        db.session.commit()

        log_activity(
            current_user.user_id,
            "Chatbot Interaction",
            f"Student asked a {message_type} question."
        )

        return redirect(url_for("chatbot.index"))

    chat_history = ChatMessage.query.filter_by(
        user_id=current_user.user_id
    ).order_by(
        ChatMessage.created_at.desc()
    ).limit(10).all()

    chat_history.reverse()

    return render_template("chatbot/index.html", chat_history=chat_history)

@chatbot_bp.route("/clear", methods=["POST"])
@login_required
def clear_history():
    """User-initiated removal of their own saved chat records only."""
    deleted_count = ChatMessage.query.filter_by(
        user_id=current_user.user_id
    ).delete(synchronize_session=False)
    db.session.commit()
    # Audit event does not contain chat content.
    log_activity(current_user.user_id, "Chat History Cleared", "Student cleared stored conversations.")
    flash(f"Cleared {deleted_count} saved conversation(s).", "success")
    return redirect(url_for("chatbot.index"))
