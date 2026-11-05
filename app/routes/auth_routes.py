from datetime import datetime
import hashlib
from email.utils import parseaddr

from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user import User
from app.services.analytics_service import log_activity


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def valid_email(email):
    # Basic server-side format check. Browser-side input validation is not sufficient.
    _, address = parseaddr(email)
    return (
        address == email
        and len(email) <= 120
        and "@" in email
        and "." in email.rsplit("@", 1)[-1]
        and not any(char.isspace() for char in email)
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("lecturer.index" if current_user.role == "lecturer" else "dashboard.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        university = request.form.get("university", "").strip()
        age_input = request.form.get("age", "").strip()

        if not (1 <= len(full_name) <= 100) or not valid_email(email):
            flash("Enter a valid name and email address.", "danger")
            return redirect(url_for("auth.register"))

        if not (8 <= len(password) <= 128):
            flash("Password must contain between 8 and 128 characters.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if len(university) > 150:
            flash("University name is too long.", "danger")
            return redirect(url_for("auth.register"))

        age = None
        if age_input:
            try:
                age = int(age_input)
            except ValueError:
                flash("Age must be a whole number.", "danger")
                return redirect(url_for("auth.register"))
            if age < 18 or age > 25:
                flash("The current registration age range is 18 to 25.", "danger")
                return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("An account already exists with this email.", "warning")
            return redirect(url_for("auth.register"))

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            university=university or None,
            age=age,
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Unable to register. Check whether this email already exists.", "danger")
            return redirect(url_for("auth.register"))

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("lecturer.index" if current_user.role == "lecturer" else "dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first() if email else None

        if user and user.is_active and check_password_hash(user.password_hash, password):
            login_user(user)
            session['_password_fp'] = hashlib.sha256(user.password_hash.encode('utf-8')).hexdigest()
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity(user.user_id, "Login", "User logged into EduMind AI.")
            flash("Login successful.", "success")
            return redirect(url_for("lecturer.index" if current_user.role == "lecturer" else "dashboard.index"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
