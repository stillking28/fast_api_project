import os
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repository import DB_FILE

client = TestClient(app)
TEST_API_KEY = os.getenv("API_KEY")
if not TEST_API_KEY:
    raise ValueError("Не найден API_KEY в переменных окружения для тестирования.")
HEADERS = {"MY-API-KEY": TEST_API_KEY}


@pytest.fixture(autouse=True)
def cleanup_db():
    with open(DB_FILE, "w") as f:
        json.dump({}, f)
    yield
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Ping pong"}


def test_read_users_no_auth():
    response = client.get("/users/")
    assert response.status_code == 403
    assert response.json() == {"detail": "Неверный или просроченный API ключ"}


def test_create_user_and_read():
    user_data = {
        "last_name": "Петров",
        "first_name": "Иван",
        "middle_name": "Иванович",
        "iin": "123456789012",
        "phone_number": "870712345678"
    }
    response = client.post("/users/", json=user_data, headers=HEADERS)
    assert response.status_code == 422
    assert "Номер телефона должен соответствовать формату" in response.text


def test_search_user():
    client.post("/users/", json={
        "last_name": "Сидоров",
        "first_name": "Петр",
        "middle_name": "Петрович",
        "iin": "987654321098",
        "phone_number": "+7 707 123 45 67" 
    }, headers=HEADERS)
    client.post("/users/", json={
        "last_name": "Иванов",
        "first_name": "Сергей",
        "middle_name": "Сергеевич",
        "iin": "876543210987",
        "phone_number": "+7 707 765 43 21"
    }, headers=HEADERS)
    response = client.get("/users/search/?q=9876", headers=HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["first_name"] == "Петр"

    response = client.get("/users/search/?q=Сергей", headers=HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["last_name"] == "Иванов"  
    