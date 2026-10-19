# Instrucciones para reproducir pruebas y evidencias

## Requisitos

- Python 3.10+
- Entorno virtual del proyecto (`.venv`)
- Dependencias de desarrollo: `pip install -r requirements-dev.txt`

## Análisis estático (Ruff)

Desde la raíz del repositorio. El diagnóstico inicial comparable (13 errores) usó exactamente:

```powershell
.\.venv\Scripts\Activate.ps1
ruff check backend/app ml --output-format=concise
```

Revisión específica de `main.py` (no sustituye al alcance anterior):

```powershell
ruff check backend/app/main.py --output-format=concise
```

## Pruebas automatizadas (pytest)

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

Las pruebas **mockean** la inferencia CNN y Supabase; no requieren reentrenar el modelo ni claves reales. Detalle de advertencias: `docs/mantenimiento/evidencias/warnings_pytest.txt`.

## Arranque manual

Backend (raíz del proyecto):

```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Comprobar salud: `GET http://127.0.0.1:8000/api/health`

## Evidencias guardadas

Ver carpeta `docs/mantenimiento/evidencias/`.
