"""
Entrenamiento CNN multiclase — PlantVillage (14 clases).

Uso:
    python ml/train.py

Variables de entorno opcionales:
    EPOCHS=12  BATCH_SIZE=32  IMG_SIZE=128
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.config import (  # noqa: E402
    BATCH_SIZE,
    CHECKPOINT_PATH,
    CLASS_NAMES,
    DATA_DIR,
    EPOCHS,
    FOLDER_MAP,
    HISTORY_PATH,
    IMG_SIZE,
    LABELS_PATH,
    MODEL_PATH,
    MODELS_DIR,
    SEED,
    VALIDATION_SPLIT,
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def collect_dataset() -> pd.DataFrame:
    rows = []
    for label, folder_name in FOLDER_MAP.items():
        class_dir = DATA_DIR / folder_name
        if not class_dir.is_dir():
            raise FileNotFoundError(f"Carpeta no encontrada: {class_dir}")
        for path in class_dir.rglob("*"):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                rows.append({"filepath": str(path), "label": label})
    if not rows:
        raise RuntimeError("No se encontraron imágenes en PlantVillage.")
    df = pd.DataFrame(rows)
    print(f"Total imágenes: {len(df)} | Clases: {df['label'].nunique()}")
    return df


def build_model(num_classes: int, input_shape: tuple[int, int, int]) -> keras.Model:
    model = keras.Sequential(
        [
            layers.Input(shape=input_shape),
            layers.Conv2D(32, (3, 3), activation="relu", padding="same"),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.2),
            layers.Conv2D(64, (3, 3), activation="relu", padding="same"),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            layers.Conv2D(128, (3, 3), activation="relu", padding="same"),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.3),
            layers.Conv2D(256, (3, 3), activation="relu", padding="same"),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.35),
            layers.Flatten(),
            layers.Dense(256, activation="relu"),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation="softmax"),
        ],
        name="plant_disease_cnn",
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main() -> None:
    img_size = int(os.getenv("IMG_SIZE", str(IMG_SIZE[0])))
    img_shape = (img_size, img_size)
    batch_size = int(os.getenv("BATCH_SIZE", str(BATCH_SIZE)))
    epochs = int(os.getenv("EPOCHS", str(EPOCHS)))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = collect_dataset()
    train_df, val_df = train_test_split(
        df,
        test_size=VALIDATION_SPLIT,
        stratify=df["label"],
        random_state=SEED,
    )

    label_to_index = {name: i for i, name in enumerate(CLASS_NAMES)}

    train_gen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=25,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.1,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode="nearest",
    )
    val_gen = ImageDataGenerator(rescale=1.0 / 255)

    train_flow = train_gen.flow_from_dataframe(
        train_df,
        x_col="filepath",
        y_col="label",
        target_size=img_shape,
        batch_size=batch_size,
        class_mode="categorical",
        classes=CLASS_NAMES,
        shuffle=True,
        seed=SEED,
    )
    val_flow = val_gen.flow_from_dataframe(
        val_df,
        x_col="filepath",
        y_col="label",
        target_size=img_shape,
        batch_size=batch_size,
        class_mode="categorical",
        classes=CLASS_NAMES,
        shuffle=False,
    )

    model = build_model(len(CLASS_NAMES), (*img_shape, 3))
    model.summary()

    callbacks = [
        EarlyStopping(
            monitor="val_accuracy",
            patience=4,
            restore_best_weights=True,
            verbose=1,
        ),
        ModelCheckpoint(
            filepath=str(CHECKPOINT_PATH),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
    ]

    history = model.fit(
        train_flow,
        validation_data=val_flow,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluación final
    eval_loss, eval_acc = model.evaluate(val_flow, verbose=0)
    print(f"\nAccuracy validación: {eval_acc:.4f} | Loss: {eval_loss:.4f}")

    # Guardar modelo final y metadatos
    model.save(MODEL_PATH)
    print(f"Modelo guardado en: {MODEL_PATH}")

    labels_meta = {
        "class_names": CLASS_NAMES,
        "label_to_index": label_to_index,
        "display_names": {
            name: name.replace("_", " ").replace("  ", " ")
            for name in CLASS_NAMES
        },
        "img_size": list(img_shape),
        "num_classes": len(CLASS_NAMES),
        "val_accuracy": float(eval_acc),
        "val_loss": float(eval_loss),
    }
    LABELS_PATH.write_text(json.dumps(labels_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    HISTORY_PATH.write_text(
        json.dumps({k: [float(v) for v in vals] for k, vals in history.history.items()}, indent=2),
        encoding="utf-8",
    )
    print("Entrenamiento completado.")


if __name__ == "__main__":
    main()
