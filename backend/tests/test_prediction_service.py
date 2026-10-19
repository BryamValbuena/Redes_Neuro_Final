"""Pruebas unitarias de las funciones extraídas en prediction_service."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.app.prediction_service import (
    build_predict_response,
    get_model_status,
    get_predictor_or_503,
    try_persist_prediction,
    validate_image_upload,
)


class TestValidateImageUpload:
    def test_accepts_image(self) -> None:
        validate_image_upload("image/png", b"abc")

    def test_rejects_missing_content_type(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_image_upload(None, b"abc")
        assert exc.value.status_code == 400

    def test_rejects_non_image(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_image_upload("application/pdf", b"abc")
        assert exc.value.status_code == 400

    def test_rejects_oversized(self) -> None:
        with patch("backend.app.prediction_service.MAX_UPLOAD_MB", 0):
            with pytest.raises(HTTPException) as exc:
                validate_image_upload("image/jpeg", b"x")
        assert exc.value.status_code == 400


class TestGetPredictorOr503:
    def test_returns_predictor(self) -> None:
        predictor = MagicMock()
        with patch("backend.app.prediction_service.get_predictor", return_value=predictor):
            assert get_predictor_or_503() is predictor

    def test_raises_503_when_missing(self) -> None:
        with patch(
            "backend.app.prediction_service.get_predictor",
            side_effect=FileNotFoundError("missing"),
        ):
            with pytest.raises(HTTPException) as exc:
                get_predictor_or_503()
        assert exc.value.status_code == 503


class TestGetModelStatus:
    def test_loaded(self) -> None:
        predictor = MagicMock()
        predictor.labels = {"class_names": ["a", "b"]}
        with patch("backend.app.prediction_service.get_predictor", return_value=predictor):
            loaded, n = get_model_status()
        assert loaded is True
        assert n == 2

    def test_missing(self) -> None:
        with patch(
            "backend.app.prediction_service.get_predictor",
            side_effect=FileNotFoundError("missing"),
        ):
            loaded, n = get_model_status()
        assert loaded is False
        assert n is None


class TestTryPersistPrediction:
    def test_warning_when_supabase_disabled(self) -> None:
        with patch("backend.app.prediction_service.is_supabase_configured", return_value=False):
            saved, warning = try_persist_prediction(
                username="admin",
                image_name="a.jpg",
                result={"disease": "X", "confidence": 1.0, "processing_time_ms": 1.0},
                image_size_bytes=10,
            )
        assert saved is None
        assert warning is not None
        assert "Supabase" in warning

    def test_saves_when_configured(self) -> None:
        record = {"id": "xyz"}
        with (
            patch("backend.app.prediction_service.is_supabase_configured", return_value=True),
            patch("backend.app.prediction_service.save_prediction", return_value=record),
        ):
            saved, warning = try_persist_prediction(
                username="admin",
                image_name="a.jpg",
                result={"disease": "X", "confidence": 1.0, "processing_time_ms": 1.0},
                image_size_bytes=10,
            )
        assert saved == record
        assert warning is None

    def test_returns_error_warning_on_failure(self) -> None:
        with (
            patch("backend.app.prediction_service.is_supabase_configured", return_value=True),
            patch(
                "backend.app.prediction_service.save_prediction",
                side_effect=RuntimeError("boom"),
            ),
        ):
            saved, warning = try_persist_prediction(
                username="admin",
                image_name="a.jpg",
                result={"disease": "X", "confidence": 1.0, "processing_time_ms": 1.0},
                image_size_bytes=10,
            )
        assert saved is None
        assert warning is not None
        assert "ERROR:" in warning


class TestBuildPredictResponse:
    def test_base_response(self) -> None:
        result = {"disease": "Tomato_healthy", "confidence": 90.0}
        response = build_predict_response(
            username="admin",
            result=result,
            saved_record=None,
            storage_warning="warn",
        )
        assert response["success"] is True
        assert response["user"] == "admin"
        assert response["disease"] == "Tomato_healthy"
        assert response["warning"] == "warn"
        assert "saved" not in response

    def test_includes_saved_fields(self) -> None:
        response = build_predict_response(
            username="admin",
            result={"disease": "X"},
            saved_record={"id": "99"},
            storage_warning=None,
        )
        assert response["saved"] is True
        assert response["prediction_id"] == "99"
        assert "warning" not in response
