"""Regression checks for globally dismissible Flask flash messages."""
from flask import flash, render_template


def test_success_flash_has_dismiss_button_and_shared_script(app, client):
    @app.get("/__test_flash_success")
    def test_success():
        flash("Login successful.", "success")
        return render_template("base.html")

    response = client.get("/__test_flash_success")
    assert response.status_code == 200
    assert b'role="status"' in response.data
    assert b'alert-success flash-notification' in response.data
    assert b'data-flash-notification' in response.data
    assert b'data-dismiss-flash' in response.data
    assert b'aria-label="Dismiss notification"' in response.data
    assert b'flash_notifications.js' in response.data
    assert b"Login successful." in response.data


def test_error_flash_is_still_accessible_and_dismissible(app, client):
    @app.get("/__test_flash_error")
    def test_error():
        flash("Database unavailable. Try again later.", "danger")
        return render_template("base.html")

    response = client.get("/__test_flash_error")
    assert response.status_code == 200
    assert b'role="alert"' in response.data
    assert b'alert-danger flash-notification' in response.data
    assert b'data-dismiss-flash' in response.data
    assert b"Database unavailable. Try again later." in response.data


def test_multiple_messages_keep_individual_dismiss_buttons(app, client):
    @app.get("/__test_flash_multiple")
    def test_multiple():
        flash("One action completed.", "success")
        flash("Review your settings.", "warning")
        return render_template("base.html")

    response = client.get("/__test_flash_multiple")
    assert response.status_code == 200
    assert response.data.count(b'data-dismiss-flash') == 2
    assert b'alert-warning flash-notification' in response.data


def test_shared_asset_pauses_countdown_during_interaction_and_hidden_tabs(client):
    js = client.get("/static/js/flash_notifications.js")
    assert js.status_code == 200
    for expected in (
        b"mouseenter", b"mouseleave", b"focusin", b"focusout",
        b"visibilitychange", b"document.hidden", b"prefers-reduced-motion",
        b"success: 5000", b"danger: 12000",
    ):
        assert expected in js.data
