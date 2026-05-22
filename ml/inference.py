"""Carga del modelo guardado y predicción sobre una imagen."""
from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from tensorflow import keras

from ml.config import LABELS_PATH, MODEL_PATH


class PlantDiseasePredictor:
    def __init__(self) -> None:
        self.model: keras.Model | None = None
        self.labels: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en {MODEL_PATH}. Ejecuta: python ml/train.py"
            )
        if not LABELS_PATH.exists():
            raise FileNotFoundError(f"Etiquetas no encontradas en {LABELS_PATH}")

        self.model = keras.models.load_model(MODEL_PATH)
        self.labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))

    @property
    def img_size(self) -> tuple[int, int]:
        size = self.labels.get("img_size", [128, 128])
        return int(size[0]), int(size[1])

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize(self.img_size)
        arr = np.array(img, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Modelo no cargado")

        start = time.perf_counter()
        batch = self.preprocess(image_bytes)
        probs = self.model.predict(batch, verbose=0)[0]
        elapsed_ms = (time.perf_counter() - start) * 1000

        idx = int(np.argmax(probs))
        class_names: list[str] = self.labels["class_names"]
        display_names: dict[str, str] = self.labels.get("display_names", {})

        disease = class_names[idx]
        return {
            "disease": disease,
            "disease_display": display_names.get(disease, disease.replace("_", " ")),
            "confidence": round(float(probs[idx]) * 100, 2),
            "processing_time_ms": round(elapsed_ms, 2),
            "top3": [
                {
                    "disease": class_names[i],
                    "disease_display": display_names.get(class_names[i], class_names[i]),
                    "confidence": round(float(probs[i]) * 100, 2),
                }
                for i in np.argsort(probs)[::-1][:3]
            ],
        }


_predictor: PlantDiseasePredictor | None = None


def get_predictor() -> PlantDiseasePredictor:
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
