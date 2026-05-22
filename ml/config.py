"""Configuración central del entrenamiento y rutas del modelo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "PlantVillage"
MODELS_DIR = ROOT / "ml" / "models"
LABELS_PATH = MODELS_DIR / "labels.json"
MODEL_PATH = MODELS_DIR / "plant_disease_cnn.keras"
CHECKPOINT_PATH = MODELS_DIR / "checkpoint_best.keras"
HISTORY_PATH = MODELS_DIR / "training_history.json"

IMG_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 12
VALIDATION_SPLIT = 0.2
SEED = 42

# Nombre canónico (API/frontend) -> carpeta real en PlantVillage
FOLDER_MAP = {
    "Tomato_Bacterial_spot": "Tomato_Bacterial_spot",
    "Tomato_Early_blight": "Tomato_Early_blight",
    "Tomato_Late_blight": "Tomato_Late_blight",
    "Tomato_Leaf_Mold": "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot": "Tomato_Septoria_leaf_spot",
    "Tomato_Target_Spot": "Tomato__Target_Spot",
    "Tomato_Tomato_mosaic_virus": "Tomato__Tomato_mosaic_virus",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato_healthy": "Tomato_healthy",
    "Potato_Early_blight": "Potato___Early_blight",
    "Potato_Late_blight": "Potato___Late_blight",
    "Potato_healthy": "Potato___healthy",
    "Pepper__bell___Bacterial_spot": "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy": "Pepper__bell___healthy",
}

CLASS_NAMES = list(FOLDER_MAP.keys())
