# PlantAI — Clasificación multiclase de enfermedades en plantas

Proyecto de **red neuronal convolucional (CNN)** con **TensorFlow/Keras**, dataset **PlantVillage**, API **FastAPI** y frontend **React + Vite + TailwindCSS**.

## Estructura del proyecto

```
Proyecto Final/
├── PlantVillage/              # Dataset (14 carpetas de clases)
├── ml/
│   ├── config.py              # Rutas, clases, mapeo de carpetas
│   ├── train.py               # Entrenamiento CNN + guardado .keras
│   ├── inference.py           # Carga del modelo y predicción
│   └── models/
│       ├── plant_disease_cnn.keras   # Modelo entrenado (generado)
│       ├── labels.json               # Metadatos de clases
│       └── checkpoint_best.keras     # Mejor época (ModelCheckpoint)
├── backend/
│   ├── app/
│   │   ├── main.py            # API: login, predict, health
│   │   ├── auth.py            # JWT login básico (sin BD)
│   │   └── config.py          # Variables de entorno
│   └── requirements.txt
├── frontend/                  # React + Vite + Tailwind
│   └── src/
│       ├── pages/             # Login, Home, Diagnose
│       ├── api/client.js      # Cliente HTTP
│       └── context/AuthContext.jsx
└── requirements.txt
```

## Clases (14)

Tomate (9), Papa (3), Pimiento (2). Los nombres de carpeta en el dataset pueden variar (`Tomato__Target_Spot`, `Potato___healthy`); el mapeo está en `ml/config.py`.

## Requisitos

- Python 3.10+
- Node.js 18+

## 1. Entrenar la red neuronal

```powershell
cd "c:\Universidad\Redes Neuronales\Proyecto Final"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ml/train.py
```

El script:

- Usa **ImageDataGenerator** con **data augmentation**
- CNN: Conv2D, MaxPooling2D, BatchNormalization, Dropout, Dense, **softmax**
- Loss: **categorical_crossentropy**
- Callbacks: **EarlyStopping**, **ModelCheckpoint**
- Guarda `ml/models/plant_disease_cnn.keras` y `labels.json`

Variables opcionales: `EPOCHS=12`, `BATCH_SIZE=32`, `IMG_SIZE=128`.

## 2. Iniciar la API

```powershell
# Copiar credenciales (opcional)
copy backend\.env.example backend\.env

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Login demo:** usuario `admin`, contraseña `plantai2025` (ver `backend/.env.example`).

## 3. Iniciar el frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173 — el proxy de Vite redirige `/api` al backend.

## Flujo de uso

1. **Login** → token JWT en `localStorage`
2. **Home** → estado del modelo
3. **Diagnóstico** → subir imagen → vista previa → **Analizar con IA**
4. Resultado: enfermedad, confianza %, tiempo (ms), top 3

## API (para deployment futuro)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/health` | No | Estado y si el modelo está cargado |
| POST | `/api/auth/login` | No | `{username, password}` → JWT |
| POST | `/api/predict` | Bearer | `multipart/form-data` campo `file` |
| GET | `/api/labels` | Bearer | Lista de clases |

## Preparación para la nube (sin implementar aún)

- **Backend:** subir carpeta `backend/` + `ml/models/` (modelo ya entrenado, sin re-entrenar)
- **Frontend:** `npm run build` → servir `frontend/dist` (Vercel, Netlify, S3)
- Definir `VITE_API_URL` apuntando a la API en producción
- Cambiar `JWT_SECRET` y credenciales en variables de entorno del host
- Añadir origen del frontend en `CORS_ORIGINS`

## Archivos importantes

| Archivo | Rol |
|---------|-----|
| `ml/train.py` | Entrenamiento completo y guardado automático |
| `ml/inference.py` | Carga `.keras` y predicción |
| `backend/app/main.py` | Puente React ↔ modelo |
| `frontend/src/pages/Diagnose.jsx` | UI de subida y resultados |

## Notas

- No se usa base de datos ni Supabase (por diseño actual).
- Si falta el modelo, la API responde 503 y el Home muestra aviso.
- Para mejor accuracy, aumenta `EPOCHS` o `IMG_SIZE` en `ml/config.py` y vuelve a entrenar una sola vez; el deploy solo necesita los archivos en `ml/models/`.
