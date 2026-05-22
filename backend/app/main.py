"""
API FastAPI — login básico + predicción de enfermedades en plantas.

Ejecutar desde la raíz del proyecto:
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.auth import create_access_token, get_current_user, verify_credentials
from backend.app.config import CORS_ORIGINS, MAX_UPLOAD_MB
from ml.inference import get_predictor

app = FastAPI(
    title="Plant Disease Detector API",
    description="Clasificación multiclase PlantVillage — preparado para deployment",
    version="1.0.0",
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


@app.on_event("startup")
def warmup_model() -> None:
    try:
        get_predictor()
    except FileNotFoundError:
        pass  # El modelo se entrena con ml/train.py


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        predictor = get_predictor()
        return HealthResponse(
            status="ok",
            model_loaded=True,
            num_classes=len(predictor.labels.get("class_names", [])),
        )
    except FileNotFoundError:
        return HealthResponse(status="ok", model_loaded=False)


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
    return {"success": True, "user": username, **result}


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
