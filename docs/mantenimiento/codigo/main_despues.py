"""
API FastAPI — login básico + predicción + historial Supabase.

Ejecutar desde la raíz del proyecto:
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.auth import create_access_token, get_current_user, verify_credentials
from backend.app.config import CORS_ORIGINS, HISTORY_DEFAULT_LIMIT
from backend.app.database import get_prediction_history
from backend.app.prediction_service import (
    build_predict_response,
    get_labels_payload,
    get_model_status,
    get_predictor_or_503,
    try_persist_prediction,
    validate_image_upload,
)
from backend.app.schemas import (
    HealthResponse,
    HistoryResponse,
    LoginRequest,
    LoginResponse,
)
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
    model_loaded, num_classes = get_model_status()
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
    content = await file.read()
    validate_image_upload(file.content_type, content)

    predictor = get_predictor_or_503()
    result = predictor.predict(content)
    image_name = file.filename or "upload.jpg"

    saved_record, storage_warning = try_persist_prediction(
        username=username,
        image_name=image_name,
        result=result,
        image_size_bytes=len(content),
    )
    return build_predict_response(
        username=username,
        result=result,
        saved_record=saved_record,
        storage_warning=storage_warning,
    )


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
def labels(_username: str = Depends(get_current_user)) -> dict:
    return get_labels_payload()
