import pytest

from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"DevSecOps Demo" in response.data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "running"
    assert "python_version" in data


def test_greet(client):
    response = client.get("/api/greet/Shubham")
    assert response.status_code == 200
    assert "Shubham" in response.get_json()["message"]


def test_add_numbers(client):
    response = client.post("/api/add", json={"number1": 10, "number2": 20})
    assert response.status_code == 200
    assert response.get_json()["result"] == 30


def test_add_numbers_missing_field(client):
    response = client.post("/api/add", json={"number1": 5})
    assert response.status_code == 400


def test_add_numbers_not_a_number(client):
    response = client.post("/api/add", json={"number1": "abc", "number2": 1})
    assert response.status_code == 400


def test_unknown_route(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
