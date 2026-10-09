from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Test Activity"
EXISTING_EMAIL = "existing@example.com"
NEW_EMAIL = "new@example.com"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            ACTIVITY_NAME: {
                "description": "A test activity",
                "schedule": "Fridays at 3 PM",
                "max_participants": 3,
                "participants": [EXISTING_EMAIL],
            }
        },
    )

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = {
        ACTIVITY_NAME: {
            "description": "A test activity",
            "schedule": "Fridays at 3 PM",
            "max_participants": 3,
            "participants": [EXISTING_EMAIL],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    activity_path = quote(ACTIVITY_NAME, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {NEW_EMAIL} for {ACTIVITY_NAME}"
    }
    assert app_module.activities[ACTIVITY_NAME]["participants"] == [
        EXISTING_EMAIL,
        NEW_EMAIL,
    ]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_path = quote(ACTIVITY_NAME, safe="")
    participants_before = list(app_module.activities[ACTIVITY_NAME]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup", params={"email": EXISTING_EMAIL}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert app_module.activities[ACTIVITY_NAME]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_path = quote("Unknown Activity", safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    # Arrange
    activity_path = quote(ACTIVITY_NAME, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": EXISTING_EMAIL},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_EMAIL} from {ACTIVITY_NAME}"
    }
    assert app_module.activities[ACTIVITY_NAME]["participants"] == []


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity_path = quote(ACTIVITY_NAME, safe="")
    participants_before = list(app_module.activities[ACTIVITY_NAME]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": NEW_EMAIL},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert app_module.activities[ACTIVITY_NAME]["participants"] == participants_before


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_path = quote("Unknown Activity", safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": EXISTING_EMAIL},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}