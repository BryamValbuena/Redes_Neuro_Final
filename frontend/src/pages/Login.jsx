import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { login as apiLogin } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiLogin(username, password);
      login(data.access_token, data.username);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <div
        className="absolute inset-0 bg-gradient-to-br from-leaf-900/40 via-soil-900 to-soil-900"
        aria-hidden
      />
      <div
        className="absolute top-1/4 -left-32 w-96 h-96 rounded-full bg-leaf-600/10 blur-3xl"
        aria-hidden
      />
      <div
        className="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl"
        aria-hidden
      />

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3" aria-hidden>
            🌱
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-stone-100">PlantAI</h1>
          <p className="text-stone-500 mt-2 text-sm">
            Detección inteligente de enfermedades en cultivos
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-stone-900/90 border border-stone-800 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-black/40 space-y-5"
        >
          {error && (
            <div className="text-sm text-red-400 bg-red-950/50 border border-red-900/50 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-stone-400 mb-1.5">
              Usuario
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-stone-950 border border-stone-700 focus:border-leaf-500 focus:ring-1 focus:ring-leaf-500 outline-none transition"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-stone-400 mb-1.5">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-stone-950 border border-stone-700 focus:border-leaf-500 focus:ring-1 focus:ring-leaf-500 outline-none transition"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-leaf-600 hover:bg-leaf-500 disabled:opacity-50 font-semibold text-white transition-colors"
          >
            {loading ? "Entrando…" : "Iniciar sesión"}
          </button>

          <p className="text-xs text-stone-600 text-center">
            Demo: usuario <code className="text-stone-500">admin</code> · ver{" "}
            <code className="text-stone-500">backend/.env.example</code>
          </p>
        </form>
      </div>
    </div>
  );
}
