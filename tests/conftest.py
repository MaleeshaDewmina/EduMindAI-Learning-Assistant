import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-secret-key-use-at-least-32-characters",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": True,
    })

    # Create the test database in its own application context.
    with app.app_context():
        db.create_all()

    # Do not keep the application context open during tests.
    # Each test request must have its own login state.
    yield app

    # Clean up the test database after the test finishes.
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()