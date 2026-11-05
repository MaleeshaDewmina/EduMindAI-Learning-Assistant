"""Student-granted, read-only lecturer reports; no chatbot or free-text access."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.models.lecturer_access_grant import LecturerAccessGrant
from app.services.lecturer_reporting import report_for_student

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer")


def lecturer_only(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "lecturer":
            abort(403)
        return fn(*args, **kwargs)
    return wrapped


def student_only(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "student":
            abort(403)
        return fn(*args, **kwargs)
    return wrapped


@lecturer_bp.route("/")
@lecturer_only
def index():
    grants = (LecturerAccessGrant.query
        .filter_by(lecturer_id=current_user.user_id)
        .order_by(LecturerAccessGrant.granted_at.desc()).all())
    entries = [(grant.student, report_for_student(grant.student_id)) for grant in grants]
    return render_template("lecturer/index.html", entries=entries,
                           pre_count=sum(report["has_pre"] for _, report in entries))


@lecturer_bp.route("/students/<int:student_id>")
@lecturer_only
def student_detail(student_id):
    grant = LecturerAccessGrant.query.filter_by(
        lecturer_id=current_user.user_id, student_id=student_id,
    ).first()
    if grant is None or grant.student.role != "student":
        abort(404)
    return render_template(
        "lecturer/student_detail.html",
        student=grant.student, report=report_for_student(student_id),
        email_allowed=bool(grant.email_allowed),
    )


@lecturer_bp.route("/sharing")
@student_only
def sharing():
    grants = LecturerAccessGrant.query.filter_by(student_id=current_user.user_id).order_by(
        LecturerAccessGrant.granted_at.desc()).all()
    return render_template("lecturer/sharing.html", grants=grants)


@lecturer_bp.route("/sharing/grant", methods=["POST"])
@student_only
def grant_access():
    email = request.form.get("lecturer_email", "").strip().lower()
    if not email or len(email) > 120:
        flash("Enter a valid lecturer account email.", "danger")
        return redirect(url_for("lecturer.sharing"))
    lecturer = User.query.filter_by(email=email, role="lecturer", is_active=True).first()
    if lecturer is None:
        flash("No authorised lecturer account was found with that email.", "warning")
        return redirect(url_for("lecturer.sharing"))
    already = LecturerAccessGrant.query.filter_by(
        student_id=current_user.user_id, lecturer_id=lecturer.user_id).first()
    if already:
        flash("This lecturer already has access. You can revoke it below.", "info")
    else:
        db.session.add(LecturerAccessGrant(student_id=current_user.user_id,
                                           lecturer_id=lecturer.user_id))
        try:
            db.session.commit()
            flash("Report access granted. You can revoke access at any time.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Access was already granted. Refresh the page.", "info")
    return redirect(url_for("lecturer.sharing"))


@lecturer_bp.route("/sharing/revoke/<int:grant_id>", methods=["POST"])
@student_only
def revoke_access(grant_id):
    grant = LecturerAccessGrant.query.filter_by(
        grant_id=grant_id, student_id=current_user.user_id).first_or_404()
    db.session.delete(grant)
    db.session.commit()
    flash("Lecturer report access revoked.", "success")
    return redirect(url_for("lecturer.sharing"))


@lecturer_bp.route("/sharing/email-permission/<int:grant_id>", methods=["POST"])
@student_only
def email_permission(grant_id):
    grant = LecturerAccessGrant.query.filter_by(
        grant_id=grant_id, student_id=current_user.user_id).first_or_404()
    grant.email_allowed = request.form.get("email_allowed") == "on"
    db.session.commit()
    flash("Email report permission updated.", "success")
    return redirect(url_for("lecturer.sharing"))
