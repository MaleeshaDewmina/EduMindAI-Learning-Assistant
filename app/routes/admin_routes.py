"""Account administration with strict role boundaries and audited changes.

Super Admin: create Admin/Lecturer; suspend/activate non-superadmin accounts.
Admin: create and manage Lecturer accounts only.
Neither role can see private student content or override sharing consent.
"""
import secrets
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user import User
from app.models.activity_log import UserActivityLog
from app.routes.auth_routes import valid_email
from app.services.email_actions import request_password_reset
from app.services.email_delivery import EmailDeliveryError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def staff_only(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in ("admin", "superadmin"):
            abort(403)
        return fn(*args, **kwargs)
    return wrapped


def _can_manage(role):
    return (current_user.role == "superadmin" and role != "superadmin") or (
        current_user.role == "admin" and role == "lecturer"
    )


def _reauthenticated():
    return check_password_hash(
        current_user.password_hash, request.form.get("current_password", "")
    )


def _audit(action, target_id):
    db.session.add(UserActivityLog(
        user_id=current_user.user_id,
        activity_name=action,
        activity_details=f"Account ID {target_id}",
    ))


@admin_bp.route("/")
@staff_only
def index():
    # Limit detail rows; summary counts are aggregated without exposing student records.
    accounts = (User.query.order_by(User.created_at.desc(), User.user_id.desc())
                .limit(200).all())
    counts = {role: User.query.filter_by(role=role).count()
              for role in ("student", "lecturer", "admin", "superadmin")}
    return render_template(
        "admin/index.html", accounts=accounts, counts=counts,
        can_create_admin=current_user.role == "superadmin",
    )


@admin_bp.route("/accounts", methods=["POST"])
@staff_only
def create_account():
    role = request.form.get("role", "").strip()
    name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not _can_manage(role):
        abort(403)
    if not _reauthenticated():
        flash("Current password is incorrect. No changes were made.", "danger")
        return redirect(url_for("admin.index"))
    if not (1 <= len(name) <= 100) or not valid_email(email):
        flash("Enter a valid name and email.", "danger")
        return redirect(url_for("admin.index"))
    if User.query.filter_by(email=email).first():
        flash("This email is already registered. No account was modified.", "warning")
        return redirect(url_for("admin.index"))

    # No shared/default password: only a single-use emailed 30-minute setup link.
    unguessable_password = secrets.token_urlsafe(48)
    account = User(
        full_name=name, email=email, role=role, is_active=True,
        password_hash=generate_password_hash(unguessable_password),
    )
    db.session.add(account)
    try:
        db.session.flush()
        _audit("Admin account created", account.user_id)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Account already exists. No changes were made.", "warning")
        return redirect(url_for("admin.index"))

    try:
        request_password_reset(email)
    except EmailDeliveryError:
        flash("Account created, but invitation email could not be sent. The new user can use Forgot Password to request an access link.", "warning")
    else:
        flash("Account created. If email delivery is enabled, a 30-minute password setup link was sent to the new user's address.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/accounts/<int:user_id>/status", methods=["POST"])
@staff_only
def update_status(user_id):
    target = db.session.get(User, user_id)
    if target is None:
        abort(404)
    if target.user_id == current_user.user_id or not _can_manage(target.role):
        abort(403)
    if not _reauthenticated():
        flash("Current password is incorrect. No changes were made.", "danger")
        return redirect(url_for("admin.index"))
    desired = request.form.get("active")
    if desired not in ("true", "false"):
        abort(400)
    target.is_active = desired == "true"
    _audit("Account reactivated" if target.is_active else "Account suspended", target.user_id)
    db.session.commit()
    flash("Account status updated.", "success")
    return redirect(url_for("admin.index"))
