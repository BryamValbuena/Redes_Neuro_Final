# PlantAI — Deployment (Supabase + Render + Vercel)

Repositorio: https://github.com/BryamValbuena/Redes_Neuro_Final.git

## Requisitos previos

- Cuenta [Supabase](https://supabase.com)
- Cuenta [Render](https://render.com)
- Cuenta [Vercel](https://vercel.com)
- Modelo ya entrenado en `ml/models/plant_disease_cnn.keras` (incluido en el repo)
- Git push del proyecto a GitHub

---

## Paso 1 — Supabase: crear tabla `predictions`

1. Abre https://supabase.com/dashboard/project/xjcupfnitochxsetnbve
2. Ve a **SQL Editor** → **New query**
3. Pega y ejecuta el contenido de:

   `supabase/migrations/001_predictions.sql`

4. Verifica en **Table Editor** que existe la tabla `predictions` con columnas:
   - `id`, `user_id`, `image_name`, `predicted_class`, `confidence`, `processing_time_ms`, `estimated_processing_usage`, `created_at`

### Obtener claves API

1. **Project Settings** → **API**
2. Copia:
   - **Project URL** → `SUPABASE_URL`
   - **service_role** (secret) → `SUPABASE_SERVICE_ROLE_KEY` — solo backend Render
   - **publishable** → `SUPABASE_PUBLISHABLE_KEY` (opcional, referencia)

> **Importante:** La clave `service_role` bypass RLS. No la subas al frontend ni a GitHub.

---

## Paso 2 — GitHub

```powershell
cd "c:\Universidad\Redes Neuronales\Proyecto Final"
git init
git remote add origin https://github.com/BryamValbuena/Redes_Neuro_Final.git
git add .
git commit -m "PlantAI: Supabase historial + deployment Render/Vercel"
git branch -M main
git push -u origin main
```

Asegúrate de que `ml/models/plant_disease_cnn.keras` esté en el commit (≈52 MB). Si GitHub rechaza el tamaño, usa [Git LFS](https://git-lfs.github.com/) solo para ese archivo.

---

## Paso 3 — Backend en Render

### Opción A: Blueprint (`render.yaml`)

1. Render Dashboard → **New** → **Blueprint**
2. Conecta el repo `Redes_Neuro_Final`
3. Render detecta `render.yaml` y crea el servicio `plantai-api`

### Opción B: Web Service manual

| Campo | Valor |
|--------|--------|
| Root Directory | *(vacío — raíz del repo)* |
| Runtime | Python 3 |
| Build Command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start Command | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/api/health` |

### Variables de entorno en Render

| Variable | Valor |
|----------|--------|
| `AUTH_USERNAME` | tu usuario login |
| `AUTH_PASSWORD` | tu contraseña login |
| `JWT_SECRET` | string largo aleatorio |
| `CORS_ORIGINS` | `https://TU-APP.vercel.app` (sin barra final) |
| `SUPABASE_URL` | `https://xjcupfnitochxsetnbve.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | clave **service_role** de Supabase |

Plan recomendado: **Starter** o superior (TensorFlow necesita RAM).

Tras el deploy, prueba:

```text
GET https://plantai-api.onrender.com/api/health
```

Debe responder `"supabase_configured": true` y `"model_loaded": true`.

---

## Paso 4 — Frontend en Vercel

1. Vercel → **Add New Project** → importa `Redes_Neuro_Final`
2. Configuración:

| Campo | Valor |
|--------|--------|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

3. **Environment Variables:**

| Variable | Valor |
|----------|--------|
| `VITE_API_URL` | `https://plantai-api.onrender.com` (URL de tu API Render) |

4. Deploy

5. Copia la URL de Vercel (ej. `https://redes-neuro-final.vercel.app`) y actualiza en **Render** la variable:

   `CORS_ORIGINS=https://redes-neuro-final.vercel.app`

6. Redeploy del backend en Render si cambiaste CORS.

---

## Paso 5 — Verificación end-to-end

1. Abre la app Vercel → **Login** (`admin` / tu contraseña)
2. **Diagnóstico** → sube una imagen → analizar
3. **Historial** → debe aparecer el registro
4. En Supabase **Table Editor** → `predictions` → fila nueva

### Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado modelo + Supabase |
| POST | `/api/predict` | Predicción + guardado automático |
| GET | `/api/history?limit=50` | Historial del usuario JWT |

---

## Desarrollo local

```powershell
# backend/.env con SUPABASE_SERVICE_ROLE_KEY
copy backend\.env.example backend\.env
# Editar backend\.env y pegar service_role

.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# otra terminal
cd frontend
npm run dev
```

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| Historial 503 | Falta `SUPABASE_SERVICE_ROLE_KEY` en Render |
| CORS error | Añade URL exacta de Vercel en `CORS_ORIGINS` |
| Modelo 503 | Falta `plant_disease_cnn.keras` en el deploy |
| Render build lento | Normal por TensorFlow; usa plan con más RAM |
| Tabla vacía | Ejecuta SQL en Supabase; haz una predicción de prueba |

---

## Arquitectura producción

```text
[Vercel React] --VITE_API_URL--> [Render FastAPI] --service_role--> [Supabase Postgres]
                                        |
                                        v
                              plant_disease_cnn.keras (local en disco)
```

Login sigue siendo **JWT propio** (no Supabase Auth). `user_id` en la tabla = `username` del JWT.
