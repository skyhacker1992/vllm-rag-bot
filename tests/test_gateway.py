from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_responds():
    response = client.get("/")
    assert response.status_code in (200, 401, 403)


def test_chat_endpoint_exists():
    response = client.post(
        "/v1/chat",
        json={"message": "hello", "use_rag": False},
    )
    assert response.status_code != 404
