from fastapi.testclient import TestClient

from src.content_model_service import app

client = TestClient(app)


def test_call_content_moderation():
    response = client.post(
        "/sentences/",
        json={
            "fragment": "This is a test sentence with no foul language",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"hasFoulLanguage": False}
