import { useCallback, useEffect, useState } from "react";
import { fetchHistory } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatClass(name) {
  return name?.replace(/_/g, " ").replace(/\s+/g, " ") ?? "—";
}

export default function PredictionHistory() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchHistory(token);
      setItems(data.items ?? []);
    } catch (err) {
      setError(err.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-stone-50">Historial de predicciones</h1>
          <p className="mt-2 text-stone-500 text-sm sm:text-base">
            Diagnósticos guardados en Supabase — sincronizados con cada análisis.
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="shrink-0 px-4 py-2 rounded-xl border border-stone-700 text-sm text-stone-300 hover:border-leaf-600 hover:text-leaf-300 transition-colors disabled:opacity-50"
        >
          {loading ? "Actualizando…" : "Actualizar"}
        </button>
      </div>

      {error && (
        <div className="mb-6 text-sm text-amber-300 bg-amber-950/40 border border-amber-800/50 rounded-xl px-4 py-3">
          {error}
          <p className="text-xs text-amber-600/80 mt-2">
            Verifica que ejecutaste el SQL en Supabase y configuraste SUPABASE_SERVICE_ROLE_KEY en
            Render.
          </p>
        </div>
      )}

      {loading && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <div className="w-10 h-10 border-2 border-leaf-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-stone-500 text-sm">Cargando historial…</p>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="text-center py-16 rounded-2xl border border-dashed border-stone-700 bg-stone-900/40">
          <p className="text-4xl mb-3" aria-hidden>
            📋
          </p>
          <p className="text-stone-400 font-medium">Sin predicciones aún</p>
          <p className="text-stone-600 text-sm mt-2">
            Analiza una imagen en Diagnóstico y aparecerá aquí automáticamente.
          </p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto rounded-2xl border border-stone-800 bg-stone-900/60">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-stone-800 text-stone-500 text-xs uppercase tracking-wide">
                  <th className="px-4 py-3 font-medium">Fecha</th>
                  <th className="px-4 py-3 font-medium">Imagen</th>
                  <th className="px-4 py-3 font-medium">Enfermedad</th>
                  <th className="px-4 py-3 font-medium text-right">Confianza</th>
                  <th className="px-4 py-3 font-medium text-right">Tiempo</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-stone-800/80 hover:bg-stone-800/30 transition-colors"
                  >
                    <td className="px-4 py-3 text-stone-400 whitespace-nowrap">
                      {formatDate(row.created_at)}
                    </td>
                    <td className="px-4 py-3 text-stone-300 max-w-[140px] truncate" title={row.image_name}>
                      {row.image_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium text-stone-100">
                        {formatClass(row.predicted_class)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-leaf-400 font-semibold">
                      {Number(row.confidence).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right text-stone-400">
                      {Number(row.processing_time_ms).toFixed(0)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {items.map((row) => (
              <article
                key={row.id}
                className="p-4 rounded-2xl border border-stone-800 bg-stone-900/60 space-y-3"
              >
                <div className="flex justify-between items-start gap-2">
                  <p className="font-semibold text-stone-100 leading-snug">
                    {formatClass(row.predicted_class)}
                  </p>
                  <span className="text-leaf-400 font-bold text-sm shrink-0">
                    {Number(row.confidence).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-stone-500 truncate" title={row.image_name}>
                  {row.image_name}
                </p>
                <div className="flex justify-between text-xs text-stone-500">
                  <span>{formatDate(row.created_at)}</span>
                  <span>{Number(row.processing_time_ms).toFixed(0)} ms</span>
                </div>
              </article>
            ))}
          </div>

          <p className="mt-4 text-xs text-stone-600 text-center">
            {items.length} registro{items.length !== 1 ? "s" : ""}
          </p>
        </>
      )}
    </div>
  );
}
