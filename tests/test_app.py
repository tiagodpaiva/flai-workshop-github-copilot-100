"""
Tests for the Mergington High School API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

# Snapshot of the initial activities state to restore between tests
_INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_INITIAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_contains_expected_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        expected = [
            "Soccer Team", "Basketball Club", "Drama Club", "Art Workshop",
            "Math Olympiad", "Science Club", "Chess Club", "Programming Class",
            "Gym Class",
        ]
        for name in expected:
            assert name in data, f"Expected activity '{name}' not found"

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        data = response.json()
        for name, details in data.items():
            assert "description" in details, f"Missing 'description' in {name}"
            assert "schedule" in details, f"Missing 'schedule' in {name}"
            assert "max_participants" in details, f"Missing 'max_participants' in {name}"
            assert "participants" in details, f"Missing 'participants' in {name}"


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        email = "newstudent@mergington.edu"
        client.post("/activities/Soccer Team/signup", params={"email": email})
        activities = client.get("/activities").json()
        assert email in activities["Soccer Team"]["participants"]

    def test_signup_activity_not_found(self, client):
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_already_registered(self, client):
        email = "duplicate@mergington.edu"
        client.post("/activities/Drama Club/signup", params={"email": email})
        response = client.post("/activities/Drama Club/signup", params={"email": email})
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_signup_existing_participant_rejected(self, client):
        # Chess Club already has michael@mergington.edu pre-seeded
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400

    def test_signup_returns_message(self, client):
        response = client.post(
            "/activities/Art Workshop/signup",
            params={"email": "artist@mergington.edu"},
        )
        data = response.json()
        assert "message" in data


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        # michael@mergington.edu is pre-seeded in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/unregister", params={"email": email})
        activities = client.get("/activities").json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_not_signed_up(self, client):
        response = client.delete(
            "/activities/Soccer Team/unregister",
            params={"email": "notregistered@mergington.edu"},
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_returns_message(self, client):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        data = response.json()
        assert "message" in data


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
