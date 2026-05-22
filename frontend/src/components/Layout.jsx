import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Layout() {
  const { username, logout } = useAuth();

  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? "bg-leaf-600/30 text-leaf-300"
        : "text-stone-400 hover:text-stone-100 hover:bg-stone-800/60"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-stone-800/80 bg-stone-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold text-leaf-400">
            <span className="text-2xl" aria-hidden>
              🌿
            </span>
            <span className="hidden sm:inline">PlantAI</span>
          </NavLink>
          <nav className="flex items-center gap-1 sm:gap-2">
            <NavLink to="/" end className={linkClass}>
              Inicio
            </NavLink>
            <NavLink to="/diagnose" className={linkClass}>
              Diagnóstico
            </NavLink>
            <NavLink to="/history" className={linkClass}>
              Historial
            </NavLink>
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-xs text-stone-500 hidden md:inline">{username}</span>
            <button
              type="button"
              onClick={logout}
              className="text-xs sm:text-sm px-3 py-1.5 rounded-lg border border-stone-700 text-stone-400 hover:border-leaf-600 hover:text-leaf-300 transition-colors"
            >
              Salir
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-stone-800 py-6 text-center text-xs text-stone-600">
        PlantAI · Clasificación multiclase PlantVillage · CNN TensorFlow
      </footer>
    </div>
  );
}
