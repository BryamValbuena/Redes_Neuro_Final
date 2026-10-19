# Informe técnico — Mantenimiento de Software: PlantAI

**Asignatura:** Mantenimiento de Sistemas de Software  
**Proyecto:** PlantAI — clasificación de enfermedades de plantas (CNN + FastAPI + React)  
**Repositorio:** https://github.com/BryamValbuena/Redes_Neuro_Final  
**Rama de trabajo:** `refactor/mantenimiento-api` (integrada en `main`)  
**Fecha de evidencias:** 2026-10-18  

---

## 1. Introducción y objetivo

Se aplicó un ciclo verificable de mantenimiento sobre PlantAI sin reescribir el producto: diagnóstico de olores de código, refactorización controlada, control de versiones con Git, pruebas automatizadas y evidencias reproducibles. Se conservó el contrato de la API (rutas, códigos HTTP, campos de respuesta) y se evitaron entrenamientos completos de la CNN en la suite de pruebas.

---

## 2. Descripción del proyecto y módulo seleccionado

PlantAI clasifica enfermedades vegetales (PlantVillage, 14 clases) con una CNN TensorFlow/Keras. El backend FastAPI expone autenticación JWT, predicción, historial (Supabase) y salud del modelo; el frontend es React + Vite.

**Módulo seleccionado:** `backend/app/main.py`  
**Tamaño inicial (evidencia):** **208 líneas**; función `predict` **61 líneas** (115–175).  
**Tamaño final (medición actual):** **147 líneas**; función `predict` **23 líneas** (99–121).  
**Justificación:** supera 150 líneas, concentra la API, presenta olores demostrables y permite pruebas con `TestClient` + mocks sin reentrenar.

Copias: `docs/mantenimiento/codigo/main_antes.py` y `main_despues.py`.

---

## 3. Diagnóstico de bad smells

| # | Bad smell | Ubicación (código original) | Evidencia |
|---|-----------|-----------------------------|-----------|
| 1 | **Long Method** / múltiples responsabilidades | `predict`, L115–175 (**61 líneas**) | Validaba imagen, cargaba modelo, predecía, persistía en Supabase, imprimía traceback y armaba la respuesta. |
| 2 | **Duplicated Code** | `health` L84–92, `predict` L127–133, `labels` L201–208 | Patrón repetido `try: get_predictor() except FileNotFoundError`. |
| 3 | **Manejo de errores frágil** | bloque Supabase en `predict` ~L151–160 | `print` + `traceback.print_exc()` y `f"ERROR: {str(exc)}"` (Ruff `RUF010`). |

**Antes (extracto):**

```python
# main.py original — predict()
if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
# ... tamaño, get_predictor, predict, save_prediction, print/traceback ...
```

**Después (extracto real actual):**

```python
# main.py actual — predict() orquesta helpers
content = await file.read()
validate_image_upload(file.content_type, content)
predictor = get_predictor_or_503()
result = predictor.predict(content)
saved_record, storage_warning = try_persist_prediction(...)
return build_predict_response(...)
```

---

## 4. Análisis estático (Ruff) y evidencias

**Herramienta:** Ruff 0.17.1  

**Comando comparable (diagnóstico inicial de 13 errores):**

```powershell
ruff check backend/app ml --output-format=concise
```

| Momento | Alcance | Resultado real |
|---------|---------|----------------|
| Antes | `backend/app` + `ml` | **13 errores** (`ruff_antes.txt`) |
| Después (misma alcance/comando) | `backend/app` + `ml` | **11 errores** (`ruff_despues.txt`) — **no está limpio** |
| Después (solo `main.py`) | `backend/app/main.py` | **1 error:** `B008` en `File(...)` (`ruff_despues_main.txt` / `ruff_despues_stats.txt`) |

**Errores que permanecen en el alcance completo (11):** imports en `auth.py`/`database.py`, `UP017`/`UP037`, `B008` en `Depends`/`File`, `TRY401` en `database.py`, imports no usados y `RUF100` en `ml/`. No se “limpiaron” de forma agresiva módulos ajenos al foco del taller para no introducir cambios funcionales colaterales.

**Por qué se conserva `B008` en `main.py`:** es el patrón idiomático de FastAPI (`File(...)` / `Depends(...)` en parámetros de endpoints). Forzar cero avisos exigiría un cambio de estilo (`Annotated`) no necesario para el comportamiento.

**Mejora verificada en el módulo refactorizado:** desaparecieron de `main.py` el `I001` (imports ordenados) y el `RUF010` del `str(exc)` ligado al bloque de depuración eliminado.

---

## 5. Tres técnicas de refactorización

### 5.1 Extracción de módulo (Extract Module)
Modelos Pydantic movidos a `backend/app/schemas.py`. `main.py` deja de mezclar contratos HTTP con handlers.

### 5.2 Extracción de método + DRY
Lógica en `backend/app/prediction_service.py`: `validate_image_upload`, `get_predictor_or_503`, `get_model_status`, `try_persist_prediction`, `build_predict_response`, `get_labels_payload`. Elimina el Long Method y la duplicación de carga del modelo.

### 5.3 Simplificación del manejo de errores
Se eliminó `print`/`traceback.print_exc()`; queda `logger.exception` y `f"ERROR: {exc}"` en `try_persist_prediction`, conservando la semántica de `warning` en la respuesta.

**Contrato API:** sin cambios de rutas, campos ni códigos HTTP.

---

## 6. Gestión de versiones con Git

| Elemento | Valor verificado |
|----------|------------------|
| Rama principal | `main` (HEAD actual) |
| Rama de trabajo | `refactor/mantenimiento-api` |
| Merge | `7eb6992e98b27de5557b2c0fe6b72b78ce3a0681` incluido en `main` (`--no-ff`) |

**Commits relevantes de la rama:**

1. `3053d698` — pruebas iniciales + evidencias Ruff/pytest **antes**  
2. `009d67a5` — extracción de `schemas.py`  
3. `ca43a035` — `prediction_service.py` + adelgazamiento de `main.py`  
4. `24dcc50f` — tests unitarios + evidencias **después**  
5. `796536a2` — informe técnico e instrucciones  

Evidencia: `docs/mantenimiento/evidencias/git_hashes.txt`, `git_merge.txt`.  
**No se hizo `git push`.**

---

## 7. Pruebas automatizadas y resultados

**Framework:** pytest + FastAPI `TestClient`  
**Comando final:** `pytest -v`  

| Momento | Resultado |
|---------|-----------|
| Antes (API) | **17 passed** (`pytest_antes.txt`) |
| Después (API + helpers) | **30 passed, 0 failed** (`pytest_despues.txt`) |

**Limitaciones:** no miden accuracy ni latencia real del CNN; inferencia y Supabase se mockean. En runtime local, `/api/health` confirmó `model_loaded=true`, `num_classes=14` y `supabase_configured=false`.

**Advertencias (documentadas en `warnings_pytest.txt`):**
- `asyncio_mode`: ya no aparece; se quitó de `pytest.ini` (no hay `pytest-asyncio` ni necesidad de él).
- TensorFlow `distutils` y FastAPI `on_event`: deprecaciones externas/ajenas al alcance; no se ocultaron fallando tests.

---

## 8. Reflexión final

El mantenimiento mejoró la sostenibilidad sin alterar el comportamiento observable de la API: responsabilidades separadas, helpers testeables y regresión automatizada (30 pruebas). Ruff aportó evidencia objetiva (p. ej. eliminación de `RUF010` en el flujo refactorizado), pero el alcance completo `backend/app` + `ml` **sigue con 11 avisos** — no se afirma un “cero errores” falso. En sistemas con ML, aislar la inferencia permite mantener la capa HTTP con bajo costo de ejecución.

---

## 9. Enlace al repositorio

https://github.com/BryamValbuena/Redes_Neuro_Final

---

## Anexos

| Contenido | Ruta |
|-----------|------|
| Código antes/después | `docs/mantenimiento/codigo/` |
| Ruff / pytest / Git / health | `docs/mantenimiento/evidencias/` |
| Advertencias pytest | `docs/mantenimiento/evidencias/warnings_pytest.txt` |
| Reproducción | `docs/mantenimiento/INSTRUCCIONES_REPRODUCCION.md` |

**PDF:** no regenerado. No hay `pandoc`, `wkhtmltopdf` ni `reportlab` en el entorno. El entregable editable es este Markdown (~contenido equivalente a pocas páginas; el límite de 8 páginas del PDF no pudo verificarse sobre un artefacto PDF inexistente).
