"""Fixtures compartidas para pruebas de la API PlantAI."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_predictor() -> MagicMock:
    predictor = MagicMock()
    predictor.labels = {
        "class_names": ["Tomato_healthy", "Potato___Early_blight", "Pepper__bell___Bacterial_spot"],
        "display_names": {
            "Tomato_healthy": "Tomato healthy",
            "Potato___Early_blight": "Potato Early blight",
            "Pepper__bell___Bacterial_spot": "Pepper bell Bacterial spot",
        },
    }
    predictor.predict.return_value = {
        "disease": "Tomato_healthy",
        "disease_display": "Tomato healthy",
        "confidence": 95.5,
        "processing_time_ms": 12.34,
        "top3": [
            {
                "disease": "Tomato_healthy",
                "disease_display": "Tomato healthy",
                "confidence": 95.5,
            },
            {
                "disease": "Potato___Early_blight",
                "disease_display": "Potato Early blight",
                "confidence": 3.2,
            },
            {
                "disease": "Pepper__bell___Bacterial_spot",
                "disease_display": "Pepper bell Bacterial spot",
                "confidence": 1.3,
            },
        ],
    }
    return predictor


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    from backend.app.config import AUTH_PASSWORD, AUTH_USERNAME

    response = client.post(
        "/api/auth/login",
        json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(mock_predictor: MagicMock):
    """Cliente FastAPI con modelo mockeado y sin Supabase."""
    with (
        patch("backend.app.main.get_predictor", return_value=mock_predictor),
        patch("backend.app.main.is_supabase_configured", return_value=False),
        patch("ml.inference.get_predictor", return_value=mock_predictor),
    ):
        from backend.app.main import app

        with TestClient(app) as test_client:
            yield test_client
