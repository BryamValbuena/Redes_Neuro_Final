"""Esquemas Pydantic de la API PlantAI."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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
