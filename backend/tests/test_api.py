"""Pruebas de regresión de la API FastAPI (comportamiento público)."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _tiny_png_bytes() -> bytes:
    """PNG 1x1 mínimo válido (no requiere modelo real)."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


class TestHealth:
    def test_health_ok_with_model(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is True
        assert data["num_classes"] == 3
        assert data["supabase_configured"] is False

    def test_health_without_model(self, mock_predictor: MagicMock) -> None:
        with (
            patch("backend.app.main.get_predictor", side_effect=FileNotFoundError("missing")),
            patch("backend.app.main.is_supabase_configured", return_value=False),
            patch(
                "backend.app.prediction_service.get_predictor",
                side_effect=FileNotFoundError("missing"),
            ),
            patch("ml.inference.get_predictor", side_effect=FileNotFoundError("missing")),
        ):
            from backend.app.main import app

            with TestClient(app) as c:
                response = c.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_loaded"] is False
        assert data["num_classes"] is None


class TestAuth:
    def test_login_ok(self, client: TestClient) -> None:
        from backend.app.config import AUTH_PASSWORD, AUTH_USERNAME

        response = client.post(
            "/api/auth/login",
            json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert data["username"] == AUTH_USERNAME
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 10

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        from backend.app.config import AUTH_USERNAME

        response = client.post(
            "/api/auth/login",
            json={"username": AUTH_USERNAME, "password": "wrong-password-for-test"},
        )
        assert response.status_code == 401
        assert "incorrectos" in response.json()["detail"].lower()

    def test_me_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_token(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        from backend.app.config import AUTH_USERNAME

        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"username": AUTH_USERNAME}


class TestPredict:
    def test_predict_ok(self, client: TestClient, auth_headers: dict[str, str], mock_predictor: MagicMock) -> None:
        files = {"file": ("leaf.png", BytesIO(_tiny_png_bytes()), "image/png")}
        response = client.post("/api/predict", headers=auth_headers, files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        from backend.app.config import AUTH_USERNAME

        assert data["user"] == AUTH_USERNAME
        assert data["disease"] == "Tomato_healthy"
        assert data["confidence"] == 95.5
        assert "top3" in data
        assert "warning" in data  # Supabase no configurado
        mock_predictor.predict.assert_called_once()

    def test_predict_requires_auth(self, client: TestClient) -> None:
        files = {"file": ("leaf.png", BytesIO(_tiny_png_bytes()), "image/png")}
        response = client.post("/api/predict", files=files)
        assert response.status_code == 401

    def test_predict_rejects_non_image(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        files = {"file": ("notes.txt", BytesIO(b"hola"), "text/plain")}
        response = client.post("/api/predict", headers=auth_headers, files=files)
        assert response.status_code == 400
        assert "imagen" in response.json()["detail"].lower()

    def test_predict_rejects_oversized(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        with patch("backend.app.prediction_service.MAX_UPLOAD_MB", 0):
            # 0 MB => cualquier contenido no vacío supera el límite
            files = {"file": ("leaf.png", BytesIO(_tiny_png_bytes()), "image/png")}
            response = client.post("/api/predict", headers=auth_headers, files=files)
        assert response.status_code == 400
        assert "grande" in response.json()["detail"].lower()

    def test_predict_model_missing(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        with patch(
            "backend.app.prediction_service.get_predictor",
            side_effect=FileNotFoundError("no model"),
        ):
            files = {"file": ("leaf.png", BytesIO(_tiny_png_bytes()), "image/png")}
            response = client.post("/api/predict", headers=auth_headers, files=files)
        assert response.status_code == 503
        assert "modelo" in response.json()["detail"].lower()

    def test_predict_saves_when_supabase_ok(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        saved = {"id": "abc-123"}
        with (
            patch("backend.app.prediction_service.is_supabase_configured", return_value=True),
            patch(
                "backend.app.prediction_service.save_prediction", return_value=saved
            ) as mock_save,
        ):
            files = {"file": ("leaf.png", BytesIO(_tiny_png_bytes()), "image/png")}
            response = client.post("/api/predict", headers=auth_headers, files=files)
        assert response.status_code == 200
        data = response.json()
        assert data.get("saved") is True
        assert data.get("prediction_id") == "abc-123"
        assert "warning" not in data
        mock_save.assert_called_once()


class TestHistory:
    def test_history_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/history")
        assert response.status_code == 401

    def test_history_supabase_not_configured(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        from backend.app.supabase_client import SupabaseNotConfiguredError

        with patch(
            "backend.app.main.get_prediction_history",
            side_effect=SupabaseNotConfiguredError("no supabase"),
        ):
            response = client.get("/api/history", headers=auth_headers)
        assert response.status_code == 503

    def test_history_ok(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        items = [
            {
                "id": "1",
                "user_id": "admin",
                "image_name": "a.jpg",
                "predicted_class": "Tomato_healthy",
                "confidence": 90.0,
                "processing_time_ms": 10.0,
                "estimated_processing_usage": 1.0,
                "created_at": "2026-01-01T00:00:00Z",
            }
        ]
        with patch("backend.app.main.get_prediction_history", return_value=items):
            response = client.get("/api/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert data["items"] == items


class TestLabels:
    def test_labels_ok(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/labels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "class_names" in data
        assert "display_names" in data
        assert len(data["class_names"]) == 3

    def test_labels_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/labels")
        assert response.status_code == 401
