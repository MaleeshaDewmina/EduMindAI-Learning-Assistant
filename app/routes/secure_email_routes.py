"""Post-study email enhancements: authenticated progress reports and password recovery."""
from urllib.parse import urlsplit

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, logout_user
from app.extensions import db
from app.models.user import User
from app.models.lecturer_access_grant import LecturerAccessGrant
from app.routes.auth_routes import valid_email
from app.services.lecturer_reporting import report_for_student
from app.services.email_actions import (
    request_password_reset, check_reset_token, use_reset_token,
    allow_report_send, report_email_body
)
from app.services.email_delivery import send_email, EmailDeliveryError

mail_bp = Blueprint("mail", __name__)


@mail_bp.route("/auth/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if valid_email(email):
            try:
                request_password_reset(email)
            except EmailDeliveryError:
                # Do not reveal whether an account exists.
                current_app.logger.warning("Password reset delivery unavailable")
        flash("If an eligible account exists, a reset link will be sent to its email.", "info")
        return redirect(url_for("mail.forgot_password"))

    response = current_app.make_response(render_template("auth/forgot_password.html"))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@mail_bp.route("/auth/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if not check_reset_token(token):
        flash("This link is invalid or expired. Please request a new one.", "warning")
        return redirect(url_for("mail.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 12 or len(password) > 128:
            flash("Password must contain 12–128 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif use_reset_token(token, password):
            if current_user.is_authenticated:
                logout_user()
            flash("Password updated. Please log in with your new password.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("This link has expired or was already used.", "warning")
            return redirect(url_for("mail.forgot_password"))

    response = current_app.make_response(
        render_template("auth/reset_password.html", token=token))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@mail_bp.route("/api/reports/email", methods=["POST"])
@login_required
def email_report():
    """Email only the sender's own address; never accept arbitrary destinations."""
    if current_user.role == "student":
        if request.form.get("student_id"):
            abort(403)
        student = current_user
        recipient_role = "student"
        redirect_to = "progress.index"
        redirect_args = {}
    elif current_user.role == "lecturer":
        raw_id = request.form.get("student_id", "")
        if not raw_id.isdecimal():
            abort(400)
        student_id = int(raw_id)
        grant = LecturerAccessGrant.query.filter_by(
            lecturer_id=current_user.user_id, student_id=student_id).first()
        if grant is None or grant.student.role != "student" or not grant.email_allowed:
            abort(404)
        student = grant.student
        recipient_role = "lecturer"
        redirect_to = "lecturer.student_detail"
        redirect_args = {"student_id": student_id}
    else:
        abort(403)

    if not allow_report_send(current_user, "report"):
        flash("Email limit reached. Try again later.", "warning")
        return redirect(url_for(redirect_to, **redirect_args))

    report = report_for_student(student.user_id)
    try:
        send_email(
            current_user.email,
            "EduMind AI — Learning progress report",
            report_email_body(student, report, recipient_role),
        )
    except EmailDeliveryError:
        current_app.logger.warning("Report email delivery unavailable")
        flash("Email delivery is unavailable. Please try again later.", "danger")
        return redirect(url_for(redirect_to, **redirect_args))
    flash("Progress report sent to your registered email.", "success")
    return redirect(url_for(redirect_to, **redirect_args))
