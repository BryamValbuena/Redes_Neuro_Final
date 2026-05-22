"""Persistencia de predicciones en Supabase."""
from __future__ import annotations

import logging
from typing import Any

from backend.app.supabase_client import SupabaseNotConfiguredError, get_supabase, is_supabase_configured

logger = logging.getLogger(__name__)

TABLE = "predictions"


def estimate_processing_usage(image_size_bytes: int, processing_time_ms: float) -> float:
    """Métrica simple: KB de imagen + segundos de inferencia."""
    kb = image_size_bytes / 1024.0
    seconds = processing_time_ms / 1000.0
    return round(kb + seconds, 4)


def save_prediction(
    *,
    user_id: str,
    image_name: str,
    predicted_class: str,
    confidence: float,
    processing_time_ms: float,
    image_size_bytes: int,
) -> dict[str, Any] | None:
    """
    Inserta una predicción en Supabase.
    Retorna el registro insertado o None si Supabase no está configurado.
    """
    if not is_supabase_configured():
        logger.warning("Supabase no configurado; predicción no guardada en BD.")
        return None

    row = {
        "user_id": user_id,
        "image_name": image_name,
        "predicted_class": predicted_class,
        "confidence": round(confidence, 2),
        "processing_time_ms": round(processing_time_ms, 2),
        "estimated_processing_usage": estimate_processing_usage(
            image_size_bytes, processing_time_ms
        ),
    }

    try:
        client = get_supabase()
        

        response = client.table(TABLE).insert(row).execute()


        data = response.data
        if data and len(data) > 0:
            return data[0]
        return row
    except SupabaseNotConfiguredError:
        raise
    except Exception as exc:
        logger.exception("Error guardando predicción en Supabase: %s", exc)
        raise


def get_prediction_history(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Lista predicciones del usuario, más recientes primero."""
    if not is_supabase_configured():
        raise SupabaseNotConfiguredError(
            "Supabase no configurado. Añade SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY."
        )

    limit = max(1, min(limit, 200))
    client = get_supabase()
    response = (
        client.table(TABLE)
        .select(
            "id,user_id,image_name,predicted_class,confidence,"
            "processing_time_ms,estimated_processing_usage,created_at"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []
