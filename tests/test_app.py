from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client):
    activity_name = "Basketball Team"
    email = "new-student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    original_participants = list(activities[activity_name]["participants"])
    activity_path = quote(activity_name, safe="")

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"] == original_participants


def test_remove_participant(client):
    activity_name = "Basketball Team"
    email = "student-to-remove@mergington.edu"
    activity_path = quote(activity_name, safe="")
    signup_response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200

    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unregistered_email(client):
    activity_name = "Basketball Team"
    activity_path = quote(activity_name, safe="")
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": "not-registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
