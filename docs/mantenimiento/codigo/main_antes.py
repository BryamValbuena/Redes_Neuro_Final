"""
API FastAPI — login básico + predicción + historial Supabase.

Ejecutar desde la raíz del proyecto:
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.auth import create_access_token, get_current_user, verify_credentials
from backend.app.config import CORS_ORIGINS, HISTORY_DEFAULT_LIMIT, MAX_UPLOAD_MB
from backend.app.database import get_prediction_history, save_prediction
from backend.app.supabase_client import SupabaseNotConfiguredError, is_supabase_configured
from ml.inference import get_predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Plant Disease Detector API",
    description="Clasificación multiclase PlantVillage — Supabase + deployment",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    num_classes: int | None = None
    supabase_configured: bool = False


class HistoryResponse(BaseModel):
    success: bool = True
    count: int
    items: list[dict[str, Any]]


@app.on_event("startup")
def warmup_model() -> None:
    try:
        get_predictor()
        logger.info("Modelo CNN cargado desde ml/models/plant_disease_cnn.keras")
    except FileNotFoundError:
        logger.warning("Modelo no encontrado. Ejecuta python ml/train.py (solo una vez).")
    if is_supabase_configured():    
        logger.info("Supabase configurado correctamente.")
    else:
        logger.warning("Supabase no configurado — historial deshabilitado.")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    model_loaded = False
    num_classes = None
    try:
        predictor = get_predictor()
        model_loaded = True
        num_classes = len(predictor.labels.get("class_names", []))
    except FileNotFoundError:
        pass
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        num_classes=num_classes,
        supabase_configured=is_supabase_configured(),
    )


@app.post("/api/auth/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = create_access_token(body.username)
    return LoginResponse(access_token=token, username=body.username)


@app.get("/api/auth/me")
def me(username: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": username}


@app.post("/api/predict")
async def predict(
    file: UploadFile = File(...),
    username: str = Depends(get_current_user),
) -> dict:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    content = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Imagen demasiado grande (máx {MAX_UPLOAD_MB} MB)")

    try:
        predictor = get_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Modelo no entrenado. Ejecuta: python ml/train.py",
        ) from exc

    result = predictor.predict(content)
    image_name = file.filename or "upload.jpg"

    saved_record: dict[str, Any] | None = None
    storage_warning: str | None = None

    if is_supabase_configured():
        try:
            saved_record = save_prediction(
                user_id=username,
                image_name=image_name,
                predicted_class=result["disease"],
                confidence=float(result["confidence"]),
                processing_time_ms=float(result["processing_time_ms"]),
                image_size_bytes=len(content),
            )
        except Exception as exc:
            import traceback

            print("\n===== ERROR SUPABASE =====")
            traceback.print_exc()
            print("==========================\n")

            logger.exception("No se pudo guardar en Supabase")

            storage_warning = f"ERROR: {str(exc)}"
    else:
        storage_warning = "Supabase no configurado; historial no disponible."

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


@app.get("/api/history", response_model=HistoryResponse)
def history(
    username: str = Depends(get_current_user),
    limit: int = Query(default=HISTORY_DEFAULT_LIMIT, ge=1, le=200),
) -> HistoryResponse:
    try:
        items = get_prediction_history(username, limit=limit)
        return HistoryResponse(success=True, count=len(items), items=items)
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Error obteniendo historial")
        raise HTTPException(
            status_code=500,
            detail="Error al consultar el historial. Revisa logs y configuración Supabase.",
        ) from exc


@app.get("/api/labels")
def labels(username: str = Depends(get_current_user)) -> dict:
    try:
        predictor = get_predictor()
        return {
            "class_names": predictor.labels.get("class_names", []),
            "display_names": predictor.labels.get("display_names", {}),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Modelo no disponible") from exc
