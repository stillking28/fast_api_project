import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import repository

client = TestClient(app)
TEST_API_KEY = os.getenv("API_KEY")
if not TEST_API_KEY:
    raise ValueError("Не найден API_KEY в переменных окружения для тестирования.")
HEADERS = {"MY-API-KEY": TEST_API_KEY}


@pytest.fixture(autouse=True)
def cleanup_db():
    try:
        repository.create_table_if_not_exists()

        client = repository.get_clickhouse_client()
        client.command("TRUNCATE TABLE IF EXISTS users")
        yield
    finally:
        if client:
            client.command("TRUNCATE TABLE IF EXISTS users")


def create_test_user(iin: str, phone_number: str):
    user_data = {
        "last_name": "Тестов",
        "first_name": "Тест",
        "middle_name": "Тестович",
        "iin": iin,
        "phone_number": phone_number,
    }
    response = client.post("/users/", json=user_data, headers=HEADERS)
    assert response.status_code == 201
    return response.json()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ping pong" in response.json()["message"]


def test_auth_fails():
    response = client.get("/users/")
    assert response.status_code == 403
    assert "Неверный" in response.json()["detail"]


def test_create_user_and_duplicate_error():
    user = create_test_user("050928300494", "+7 707 123 45 67")
    assert user["last_name"] == "Тестов"

    user_data_dup_iin = {
        "last_name": "Другой",
        "first_name": "Пользователь",
        "middle_name": "Другович",
        "iin": "050928300494",
        "phone_number": "+7 707 765 43 21",
    }
    response_iin = client.post("/users/", json=user_data_dup_iin, headers=HEADERS)
    assert response_iin.status_code == 400
    assert "уже существует" in response_iin.json()["message"]


def test_user_not_found():
    response_get = client.get("/users/999", headers=HEADERS)
    assert response_get.status_code == 404
    assert "не найден" in response_get.json()["message"]

    response_del = client.delete("/users/999", headers=HEADERS)
    assert response_del.status_code == 404


def test_pagination():
    create_test_user("111111111111", "+7 707 111 11 11")
    create_test_user("222222222222", "+7 707 222 22 22")
    create_test_user("333333333333", "+7 707 333 33 33")

    response = client.get("/users/?limit=2", headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/users/?skip=1&limit=1", headers=HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["iin"] == "222222222222"


def test_search_and_pagination():
    create_test_user("444444444444", "+7 707 444 44 44")
    user2 = create_test_user("555555555555", "+7 707 555 55 55")
    user2_id = user2["id"]

    response_all = client.get("/users/search/?q=", headers=HEADERS)
    assert response_all.status_code == 200
    assert len(response_all.json()) == 2

    response_iin = client.get("/users/search/?q=5555", headers=HEADERS)
    assert response_iin.status_code == 200
    results = response_iin.json()
    assert len(results) == 1
    assert results[0]["id"] == user2_id


def test_generate_async_doc():
    user = create_test_user("777777777777", "+7 707 777 77 77")
    req_data = {
        "user_id": user["id"],
        "content_type": "docx",
        "callback_url": "http://test.com/callback",
    }
    response = client.post("/documents/generate/async/", json=req_data, headers=HEADERS)
    assert response.status_code == 202
    assert response.json()["message"] == "Задача по генерацию документа принята"
