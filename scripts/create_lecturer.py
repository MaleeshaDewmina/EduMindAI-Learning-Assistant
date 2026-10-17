"""Local operator-only lecturer account creation; never exposed as an HTTP route.

Usage from the project root:
    python scripts/create_lecturer.py
"""
from pathlib import Path
import getpass
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.user import User
from app.routes.auth_routes import valid_email


def main():
    print("EduMind AI — authorised lecturer provisioning (local only)")
    name = input("Lecturer full name: ").strip()
    email = input("Lecturer account email: ").strip().lower()
    if not 1 <= len(name) <= 100 or not valid_email(email):
        sys.exit("Invalid full name or email. No account created.")
    password = getpass.getpass("New lecturer password (12–128 characters): ")
    confirmation = getpass.getpass("Confirm lecturer password: ")
    if not (12 <= len(password) <= 128) or password != confirmation:
        sys.exit("Password length or confirmation invalid. No account created.")
    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            sys.exit("Email already registered; no account was changed. Use a different lecturer email.")
        account = User(full_name=name, email=email, password_hash=generate_password_hash(password), role="lecturer")
        db.session.add(account)
        db.session.commit()
    print("Lecturer account created. It can now log in using the normal login page.")


if __name__ == "__main__":
    main()
