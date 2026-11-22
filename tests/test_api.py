from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

TODAY = date(2026, 7, 15)


def payload(**overrides):
    body = {
        "location": "Riverside",
        "pm25": 62.0,
        "aqi_scale": "us_epa",
        "adults": 2,
        "children": 1,
        "commute_mode": "car",
        "commute_km": 12,
        "commute_days_per_week": 5,
        "cooking_fuel": "biomass",
        "notes": "Garden flat",
    }
    body.update(overrides)
    return body


@pytest.fixture
def client():
    settings = Settings(anthropic_api_key=None, model="test", request_timeout=1.0)
    return TestClient(create_app(settings=settings, today_provider=lambda: TODAY))


def test_index_serves_ui_with_security_headers(client):
    """The root route must return the HTML UI with a strict CSP."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Clean air" in response.text
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_all_security_headers_present(client):
    """Every security header must be attached to responses."""
    headers = client.get("/").headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert "camera=()" in headers.get("Permissions-Policy", "")


def test_static_js_served(client):
    """The bundled JavaScript must be reachable at its static URL."""
    response = client.get("/static/app.js")
    assert response.status_code == 200


def test_static_css_served(client):
    """The stylesheet must be reachable at its static URL."""
    response = client.get("/static/styles.css")
    assert response.status_code == 200


def test_advice_returns_complete_plan(client):
    body = client.post("/api/advice", json=payload()).json()
    assert body["risk_level"] == 3  # 62 µg/m³ is "Unhealthy"
    assert body["summary_source"] == "template"
    assert body["impacts"] and body["routines"] and body["indoor_hacks"] and body["alternatives"]
    assert body["disclaimer"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"pm25": -1},
        {"pm25": 5000},
        {"aqi_scale": "made_up"},
        {"commute_days_per_week": 9},
        {"location": "   "},
        {"is_admin": True},
        {"notes": "x" * 501},
    ],
)
def test_invalid_input_is_rejected(client, overrides):
    assert client.post("/api/advice", json=payload(**overrides)).status_code == 422


def test_control_characters_stripped_from_location(client):
    body = client.post("/api/advice", json=payload(location="River\x00side")).json()
    assert body["location"] == "River side"
