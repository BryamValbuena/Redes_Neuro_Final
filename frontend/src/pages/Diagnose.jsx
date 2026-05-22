import { useCallback, useRef, useState } from "react";
import { predictImage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Diagnose() {
  const { token } = useAuth();
  const inputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((selected) => {
    if (!selected?.type.startsWith("image/")) {
      setError("Selecciona un archivo de imagen válido.");
      return;
    }
    setError("");
    setResult(null);
    setFile(selected);
    const url = URL.createObjectURL(selected);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
  }, []);

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  async function analyze() {
    if (!file) {
      setError("Primero sube una imagen.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await predictImage(token, file);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setError("");
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  const isHealthy = result?.disease?.toLowerCase().includes("healthy");

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-stone-50">Diagnóstico por imagen</h1>
        <p className="mt-2 text-stone-500 text-sm sm:text-base">
          Sube una foto de la hoja. La CNN clasificará la enfermedad automáticamente.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
        {/* Upload + preview */}
        <div className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-8 sm:p-12 text-center transition-colors ${
              dragOver
                ? "border-leaf-500 bg-leaf-950/30"
                : "border-stone-700 hover:border-leaf-700/60 bg-stone-900/40"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
            {!preview ? (
              <>
                <div className="text-4xl mb-3">🖼️</div>
                <p className="font-medium text-stone-300">Arrastra o haz clic para subir</p>
                <p className="text-xs text-stone-600 mt-2">JPG, PNG · máx. 10 MB</p>
              </>
            ) : (
              <img
                src={preview}
                alt="Vista previa de la hoja"
                className="max-h-64 sm:max-h-80 mx-auto rounded-xl object-contain"
              />
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={analyze}
              disabled={!file || loading}
              className="flex-1 min-w-[140px] py-3 rounded-xl bg-leaf-600 hover:bg-leaf-500 disabled:opacity-50 font-semibold transition-colors"
            >
              {loading ? "Analizando…" : "Analizar con IA"}
            </button>
            <button
              type="button"
              onClick={reset}
              className="px-5 py-3 rounded-xl border border-stone-700 text-stone-400 hover:text-stone-200 transition-colors"
            >
              Limpiar
            </button>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-900/50 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </div>

        {/* Results */}
        <div className="rounded-2xl border border-stone-800 bg-stone-900/60 p-6 sm:p-8 min-h-[280px] flex flex-col">
          <h2 className="text-lg font-semibold text-stone-200 mb-4">Resultado</h2>

          {!result && !loading && (
            <p className="text-stone-600 text-sm flex-1 flex items-center justify-center text-center">
              El diagnóstico aparecerá aquí después del análisis.
            </p>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <div className="w-10 h-10 border-2 border-leaf-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-stone-500 text-sm">Procesando imagen…</p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5 flex-1">
              <div
                className={`p-4 rounded-xl border ${
                  isHealthy
                    ? "border-leaf-700/50 bg-leaf-950/40"
                    : "border-amber-800/40 bg-amber-950/20"
                }`}
              >
                <p className="text-xs uppercase tracking-wide text-stone-500 mb-1">
                  Enfermedad detectada
                </p>
                <p className="text-xl sm:text-2xl font-bold text-stone-50 leading-snug">
                  {result.disease_display}
                </p>
                <p className="text-xs text-stone-600 mt-1 font-mono">{result.disease}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-stone-950/80 border border-stone-800">
                  <p className="text-xs text-stone-500">Confianza</p>
                  <p className="text-2xl font-bold text-leaf-400">{result.confidence}%</p>
                </div>
                <div className="p-4 rounded-xl bg-stone-950/80 border border-stone-800">
                  <p className="text-xs text-stone-500">Tiempo</p>
                  <p className="text-2xl font-bold text-stone-200">
                    {result.processing_time_ms}
                    <span className="text-sm font-normal text-stone-500"> ms</span>
                  </p>
                </div>
              </div>

              {result.top3?.length > 0 && (
                <div>
                  <p className="text-xs text-stone-500 mb-2">Top 3 predicciones</p>
                  <ul className="space-y-2">
                    {result.top3.map((item) => (
                      <li
                        key={item.disease}
                        className="flex justify-between text-sm py-2 px-3 rounded-lg bg-stone-950/60"
                      >
                        <span className="text-stone-400 truncate pr-2">
                          {item.disease_display}
                        </span>
                        <span className="text-leaf-500 font-medium shrink-0">
                          {item.confidence}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
