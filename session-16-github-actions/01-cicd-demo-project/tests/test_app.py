import pytest

from app.app import app
from app.calculator import add, subtract, multiply, divide


# ---------- unit tests for calculator.py ----------

def test_add():
    assert add(10, 5) == 15


def test_subtract():
    assert subtract(10, 5) == 5


def test_multiply():
    assert multiply(10, 5) == 50


def test_divide():
    assert divide(10, 5) == 2


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


# ---------- tests for the Flask endpoints ----------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["app"] == "Session 16 CI/CD Demo"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_calc_add(client):
    response = client.get("/api/calc?op=add&a=2&b=3")
    assert response.status_code == 200
    assert response.get_json()["result"] == 5


def test_calc_divide_by_zero(client):
    response = client.get("/api/calc?op=divide&a=1&b=0")
    assert response.status_code == 400


def test_calc_unknown_op(client):
    response = client.get("/api/calc?op=power&a=2&b=3")
    assert response.status_code == 400
