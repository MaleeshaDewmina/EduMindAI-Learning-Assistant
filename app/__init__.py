from flask import Flask, redirect, url_for, request, session
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect

from config import Config
from app.extensions import db, login_manager

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    secret = app.config.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret) < 32 or secret.startswith("replace_"):
        raise RuntimeError(
            "Set a random SECRET_KEY (at least 32 characters) in your local .env file."
        )

    # Format saved AI messages safely; never mark raw model output as trusted HTML.
    from app.services.chat_formatting import format_ai_reply
    app.add_template_filter(format_ai_reply, "format_ai_reply")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Ensure that all tables are registered for ORM relationships and for tests.
    from app.models.user import User
    from app.models.study_task import StudyTask
    from app.models.progress_log import ProgressLog
    from app.models.activity_log import UserActivityLog
    from app.models.motivation_score import MotivationScore
    from app.models.chat_message import ChatMessage
    from app.models.feedback import Feedback
    from app.models.evaluation_response import EvaluationResponse
    from app.models.evaluation_item_response import EvaluationItemResponse
    from app.models.lecturer_access_grant import LecturerAccessGrant
    from app.models.email_action_event import EmailActionEvent

    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.planner_routes import planner_bp
    from app.routes.progress_routes import progress_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.routes.feedback_routes import feedback_bp
    from app.routes.evaluation_routes import evaluation_bp
    from app.routes.lecturer_routes import lecturer_bp
    from app.routes.secure_email_routes import mail_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(mail_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def check_password_session():
        # A reset invalidates every old login session for this account.
        # Hash fingerprint is stored in the signed session, not the DB.
        import hashlib
        from flask_login import logout_user
        if current_user.is_authenticated:
            if not current_user.is_active:
                logout_user()
                session.pop("_password_fp", None)
                session.pop("_role_at_login", None)
                return redirect(url_for("auth.login"))
            current_fp = hashlib.sha256(current_user.password_hash.encode('utf-8')).hexdigest()
            if (session.get('_password_fp') != current_fp
                    or session.get('_role_at_login') != current_user.role):
                logout_user()
                session.pop('_password_fp', None)
                session.pop('_role_at_login', None)
                return redirect(url_for('auth.login'))

    @app.before_request
    def lecturer_stays_in_lecturer_area():
        # All legacy student routes were originally only login-protected.
        # A lecturer may access only lecturer reports and logout, not tasks,
        # chatbot, feedback, evaluation submission, or student account pages.
        if (current_user.is_authenticated
                and current_user.role == "lecturer"
                and request.endpoint not in ("auth.logout", "static", "home", "mail.forgot_password", "mail.reset_password", "mail.email_report")
                and request.blueprint != "lecturer"):
            return redirect(url_for("lecturer.index"))

    @app.before_request
    def admins_stay_in_admin_area():
        # Other legacy routes were originally login-protected only and assume
        # every non-lecturer account is a student.
        if (current_user.is_authenticated
                and current_user.role in ("admin", "superadmin")
                and request.endpoint not in ("auth.logout", "static", "home")
                and request.blueprint != "admin"):
            return redirect(url_for("admin.index"))

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("admin.index" if current_user.role in ("admin", "superadmin")
                                    else "lecturer.index" if current_user.role == "lecturer"
                                    else "dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.after_request
    def add_security_headers(response):
        # Lightweight browser protections. Avoid an untested CSP that could
        # block the app's existing third-party styles and inline scripts.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if current_user.is_authenticated and response.mimetype == "text/html":
            # Account-specific history and evaluation pages must not be
            # shared by intermediary caches or kept as browser cache entries.
            response.headers["Cache-Control"] = "private, no-store"
        return response

    # The old unauthenticated /db-test diagnostic was removed. Never expose DB errors.
    return app
