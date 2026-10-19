"""Lógica de predicción y persistencia extraída de los endpoints FastAPI.

Centraliza validación de imágenes, carga del modelo, guardado en Supabase
y armado de respuestas para reducir duplicación en main.py.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

from backend.app.config import MAX_UPLOAD_MB
from backend.app.database import save_prediction
from backend.app.supabase_client import is_supabase_configured
from ml.inference import get_predictor

logger = logging.getLogger(__name__)

MODEL_UNAVAILABLE_DETAIL = "Modelo no entrenado. Ejecuta: python ml/train.py"
MODEL_NOT_AVAILABLE_DETAIL = "Modelo no disponible"


def validate_image_upload(content_type: str | None, content: bytes) -> None:
    """Valida tipo MIME y tamaño de la imagen subida.

    Raises:
        HTTPException: 400 si el archivo no es imagen o supera el límite.
    """
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Imagen demasiado grande (máx {MAX_UPLOAD_MB} MB)",
        )


def get_predictor_or_503(*, detail: str = MODEL_UNAVAILABLE_DETAIL):
    """Obtiene el predictor o responde HTTP 503 si el modelo no existe."""
    try:
        return get_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=detail) from exc


def get_model_status() -> tuple[bool, int | None]:
    """Estado del modelo para /api/health: (model_loaded, num_classes)."""
    try:
        predictor = get_predictor()
        num_classes = len(predictor.labels.get("class_names", []))
        return True, num_classes
    except FileNotFoundError:
        return False, None


def try_persist_prediction(
    *,
    username: str,
    image_name: str,
    result: dict[str, Any],
    image_size_bytes: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """Intenta guardar la predicción en Supabase.

    Returns:
        (registro_guardado, advertencia). Si no hay Supabase o falla el
        guardado, la predicción HTTP sigue siendo exitosa y se informa
        mediante warning (comportamiento original conservado).
    """
    if not is_supabase_configured():
        return None, "Supabase no configurado; historial no disponible."

    try:
        saved_record = save_prediction(
            user_id=username,
            image_name=image_name,
            predicted_class=result["disease"],
            confidence=float(result["confidence"]),
            processing_time_ms=float(result["processing_time_ms"]),
            image_size_bytes=image_size_bytes,
        )
        return saved_record, None
    except Exception as exc:
        logger.exception("No se pudo guardar en Supabase")
        return None, f"ERROR: {exc}"


def build_predict_response(
    *,
    username: str,
    result: dict[str, Any],
    saved_record: dict[str, Any] | None,
    storage_warning: str | None,
) -> dict[str, Any]:
    """Construye el JSON de respuesta de /api/predict sin alterar el contrato."""
    response: dict[str, Any] = {
        "success": True,
        "user": username,
        **result,
    }
    if saved_record:
        response["saved"] = True
        response["prediction_id"] = saved_record.get("id")
    if storage_warning:
        response["warning"] = storage_warning
    return response


def get_labels_payload() -> dict[str, Any]:
    """Payload de /api/labels o HTTP 503 si el modelo no está disponible."""
    predictor = get_predictor_or_503(detail=MODEL_NOT_AVAILABLE_DETAIL)
    return {
        "class_names": predictor.labels.get("class_names", []),
        "display_names": predictor.labels.get("display_names", {}),
    }
