import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Reset activities to known state for testing"""
    from src.app import activities
    # Store original activities
    original = activities.copy()

    # Reset to test data
    activities.clear()
    activities.update({
        "Test Chess Club": {
            "description": "Test chess activities",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 5,
            "participants": ["test1@mergington.edu"]
        },
        "Test Programming Class": {
            "description": "Test programming activities",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": []
        }
    })

    yield activities

    # Restore original activities
    activities.clear()
    activities.update(original)


class TestActivitiesAPI:
    """Test cases for the Activities API"""

    def test_get_activities(self, client, sample_activities):
        """Test GET /activities returns all activities"""
        response = client.get("/activities")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert len(data) == 2
        assert "Test Chess Club" in data
        assert "Test Programming Class" in data

        # Check structure of activity data
        chess_club = data["Test Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert chess_club["participants"] == ["test1@mergington.edu"]

    def test_signup_success(self, client, sample_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Test%20Programming%20Class/signup?email=test2@mergington.edu"
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test2@mergington.edu" in data["message"]
        assert "Test Programming Class" in data["message"]

        # Verify participant was added
        get_response = client.get("/activities")
        activities = get_response.json()
        assert "test2@mergington.edu" in activities["Test Programming Class"]["participants"]

    def test_signup_duplicate_participant(self, client, sample_activities):
        """Test signup fails when participant is already registered"""
        # First signup
        client.post("/activities/Test%20Chess%20Club/signup?email=test2@mergington.edu")

        # Try to signup again
        response = client.post(
            "/activities/Test%20Chess%20Club/signup?email=test2@mergington.edu"
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client, sample_activities):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_remove_participant_success(self, client, sample_activities):
        """Test successful removal of a participant"""
        # First add a participant
        client.post("/activities/Test%20Programming%20Class/signup?email=test3@mergington.edu")

        # Then remove them
        response = client.delete(
            "/activities/Test%20Programming%20Class/participants/test3@mergington.edu"
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test3@mergington.edu" in data["message"]
        assert "Test Programming Class" in data["message"]

        # Verify participant was removed
        get_response = client.get("/activities")
        activities = get_response.json()
        assert "test3@mergington.edu" not in activities["Test Programming Class"]["participants"]

    def test_remove_participant_not_found(self, client, sample_activities):
        """Test removal fails when participant is not signed up"""
        response = client.delete(
            "/activities/Test%20Chess%20Club/participants/nonexistent@mergington.edu"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]

    def test_remove_participant_invalid_activity(self, client, sample_activities):
        """Test removal fails for non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/participants/test@mergington.edu"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
