from flask import Flask, redirect, url_for
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

    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.planner_routes import planner_bp
    from app.routes.progress_routes import progress_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.routes.feedback_routes import feedback_bp
    from app.routes.evaluation_routes import evaluation_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(evaluation_bp)

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # The old unauthenticated /db-test diagnostic was removed. Never expose DB errors.
    return app
