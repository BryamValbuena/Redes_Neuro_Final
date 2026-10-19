# Informe técnico — Mantenimiento de Software: PlantAI

**Asignatura:** Mantenimiento de Sistemas de Software  
**Proyecto:** PlantAI — clasificación de enfermedades de plantas (CNN + FastAPI + React)  
**Repositorio:** https://github.com/BryamValbuena/Redes_Neuro_Final  
**Rama de trabajo:** `refactor/mantenimiento-api`  
**Fecha de evidencias:** 2026-10-18  

---

## 1. Introducción y objetivo

El objetivo de este taller fue aplicar un ciclo verificable de **mantenimiento correctivo/preventivo** sobre un sistema existente, sin reescribir el producto: diagnosticar olores de código (bad smells), refactorizar con técnicas reconocidas, registrar el trabajo en Git, automatizar pruebas de regresión y dejar evidencias reproducibles.

Se priorizó conservar el **contrato de la API** (rutas, códigos HTTP, campos de respuesta) y evitar dependencias de entrenamiento completo de la red neuronal en las pruebas.

---

## 2. Descripción del proyecto y módulo seleccionado

PlantAI clasifica enfermedades vegetales (dataset PlantVillage, 14 clases) mediante una CNN en TensorFlow/Keras. El backend FastAPI expone autenticación JWT, predicción, historial (Supabase) y salud del modelo; el frontend es React + Vite.

**Módulo seleccionado:** `backend/app/main.py`  
**Tamaño inicial:** 208 líneas (medición AST/conteo de archivo).  
**Justificación:** supera el umbral de 150 líneas, concentra la lógica de la API, presenta olores concretos demostrables y permite pruebas con `TestClient` + mocks sin reentrenar el modelo. Alternativas (`ml/train.py`, `Diagnose.jsx`) también superan 150 líneas, pero el taller se centra en mantenimiento de la capa de servicio Python/FastAPI.

---

## 3. Diagnóstico de bad smells

| # | Bad smell | Ubicación | Evidencia |
|---|-----------|-----------|-----------|
| 1 | **Long Method** (método demasiado extenso / múltiples responsabilidades) | `backend/app/main.py`, función `predict` (líneas 115–175 del original; **61 líneas**) | Un solo endpoint valida la imagen, carga el modelo, predice, persiste en Supabase, maneja errores con `print`/`traceback` y arma la respuesta HTTP. |
| 2 | **Duplicated Code** | `health` (84–92), `predict` (127–133), `labels` (201–208) | El patrón `try: get_predictor() except FileNotFoundError` se repite con variaciones de manejo (ignorar / 503 con mensajes distintos). |
| 3 | **Manejo de errores frágil / código de depuración en producción** | `predict`, bloque Supabase (aprox. 151–160) | Uso de `print` + `traceback.print_exc()` además de `logger.exception`, y `f"ERROR: {str(exc)}"` (conversión redundante detectada por Ruff `RUF010`). |

Fragmento ilustrativo del Long Method (versión original, extracto):

```python
# backend/app/main.py (antes) — predict() mezclaba validación, inferencia y persistencia
if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
# ... tamaño, get_predictor, predict, save_prediction, print/traceback, armar response ...
```

Copia completa del archivo original: `docs/mantenimiento/codigo/main_antes.py`.

---

## 4. Herramienta de análisis estático y evidencias

**Herramienta:** [Ruff](https://docs.astral.sh/ruff/) 0.17.1 (instalada en `.venv` vía `requirements-dev.txt`, sin alterar el runtime de producción).

**Comando (antes):**

```powershell
ruff check backend/app ml --output-format=concise
ruff check backend/app/main.py --select ALL --output-format=concise
```

**Resultados reales:**

| Momento | Alcance | Hallazgos relevantes |
|---------|---------|----------------------|
| Antes | `backend/app` + `ml` | **13** issues (imports, `B008`, `RUF010` en `main.py:160`, imports no usados en `ml`, etc.) |
| Antes | `main.py` con `--select ALL` | **37** avisos (incluye estilo/docstrings; evidencia en `ruff_antes_main_all.txt`) |
| Después | `main.py` + módulos nuevos | En `main.py` quedan avisos esperables de FastAPI (`B008` por `File(...)` en defaults) e imports; se eliminó el `RUF010` del `str(exc)` y el bloque `print`/`traceback`. |

Archivos de evidencia:  
`docs/mantenimiento/evidencias/ruff_antes.txt`, `ruff_antes_stats.txt`, `ruff_antes_main_all.txt`, `ruff_despues.txt`, `ruff_despues_stats.txt`, `diagnostico_inicial.txt`.

---

## 5. Técnicas de refactorización (antes / después)

### 5.1 Extracción de módulo / separación de responsabilidades (Extract Module)

- **Problema:** modelos Pydantic mezclados con rutas HTTP.  
- **Ubicación:** `main.py` líneas 46–67 (original).  
- **Cambio:** mover a `backend/app/schemas.py`.  
- **Beneficio:** `main.py` solo orquesta endpoints; esquemas reutilizables y más fáciles de probar/documentar.  
- **Prueba:** suite API (`TestHealth`, `TestAuth`, `TestHistory`) — contratos de respuesta intactos.

### 5.2 Extracción de método + eliminación de duplicación (Extract Method / DRY)

- **Problema:** Long Method en `predict` y duplicación de carga del modelo.  
- **Ubicación:** `predict` 115–175; bloques `get_predictor` en `health`/`labels`.  
- **Cambio:** crear `backend/app/prediction_service.py` con:
  - `validate_image_upload`
  - `get_predictor_or_503`
  - `get_model_status`
  - `try_persist_prediction`
  - `build_predict_response`
  - `get_labels_payload`
- **Después:** `predict` pasa de **61** a **23** líneas; `main.py` de **208** a **~147** líneas.  
- **Beneficio:** funciones con una responsabilidad, reutilización del manejo 503 del modelo.  
- **Prueba:** `backend/tests/test_prediction_service.py` + `TestPredict` en `test_api.py`.

### 5.3 Simplificación del manejo de errores (Replace Error Code / limpiar depuración)

- **Problema:** `print` + `traceback.print_exc()` y conversión redundante `str(exc)`.  
- **Ubicación:** bloque `except` de guardado Supabase en `predict`.  
- **Cambio:** un único `logger.exception(...)` y `f"ERROR: {exc}"` dentro de `try_persist_prediction`.  
- **Beneficio:** logging estructurado, sin ruido en stdout; misma semántica de `warning` en la respuesta.  
- **Prueba:** `test_returns_error_warning_on_failure` y `test_predict_saves_when_supabase_ok`.

**Contrato API:** no se modificaron rutas, nombres de campos ni códigos HTTP.

---

## 6. Gestión de versiones con Git

| Elemento | Valor |
|----------|-------|
| Rama principal | `main` |
| Rama de mantenimiento | `refactor/mantenimiento-api` |
| Política | commits pequeños; sin `reset --hard` ni operaciones destructivas |

**Commits de la rama (hashes completos en `evidencias/git_hashes.txt`):**

1. `3053d698…` — pruebas iniciales + evidencias Ruff/pytest **antes**  
2. `009d67a5…` — extracción de `schemas.py`  
3. `ca43a035…` — `prediction_service.py` + adelgazamiento de `main.py`  
4. `24dcc50f…` — tests unitarios + evidencias **después**  
5. *(commit de informe/documentación, si aplica en el historial posterior)*  

El merge a `main` se documenta en `evidencias/git_merge.txt` tras ejecutarlo.

---

## 7. Pruebas automatizadas y resultados

**Framework:** pytest + `fastapi.testclient.TestClient`  
**Estrategia:** mocks de `get_predictor`, Supabase y persistencia; **no** se entrena ni se carga el `.keras` en la suite (salvo arranque real opcional fuera de tests).

**Antes de refactorizar (solo API):**

```text
17 passed
```

Evidencia: `docs/mantenimiento/evidencias/pytest_antes.txt`

**Después (API + funciones extraídas):**

```text
30 passed, 0 failed
```

Evidencia: `docs/mantenimiento/evidencias/pytest_despues.txt`

Cobertura funcional de tests: casos normales, credenciales inválidas, archivo no imagen, tamaño excedido, modelo ausente (503), historial sin Supabase (503), persistencia exitosa mockeada, y unitarias de helpers.

**Limitación explícita:** las pruebas **no** validan accuracy del modelo CNN ni latencia real de TensorFlow; la inferencia se aísla con mocks. La carga real del modelo se verificó aparte vía `GET /api/health` en ejecución local (`model_loaded: true`, `num_classes: 14`).

---

## 8. Reflexión final

El mantenimiento aplicado no cambió la funcionalidad percibida por el cliente de la API, pero sí la **sostenibilidad**: `main.py` dejó de ser un “contenedor” de reglas de negocio, las responsabilidades quedaron nombradas y testeables, y el regreso de defectos se reduce con 30 pruebas automatizadas. La lección práctica es que, en sistemas con ML, conviene **aislar** la inferencia costosa detrás de interfaces pequeñas para poder mantener la capa HTTP con confianza y bajo costo de ejecución.

El análisis estático (Ruff) aportó evidencia objetiva (p. ej. `RUF010`) complementaria al juicio humano sobre Long Method y duplicación; no sustituye el diseño, pero ancla el diagnóstico a artefactos reproducibles.

---

## 9. Enlace al repositorio

https://github.com/BryamValbuena/Redes_Neuro_Final

---

## Anexos (rutas de evidencias)

| Contenido | Ruta |
|-----------|------|
| Código antes | `docs/mantenimiento/codigo/main_antes.py` |
| Código después | `docs/mantenimiento/codigo/main_despues.py` |
| Servicio extraído | `docs/mantenimiento/codigo/prediction_service.py` |
| Esquemas | `docs/mantenimiento/codigo/schemas.py` |
| Ruff / pytest | `docs/mantenimiento/evidencias/` |
| Reproducción | `docs/mantenimiento/INSTRUCCIONES_REPRODUCCION.md` |

**Nota PDF:** no se generó PDF porque `pandoc` no está instalado en el entorno; el entregable editable es este Markdown.
