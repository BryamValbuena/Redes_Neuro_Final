import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { checkHealth } from "../api/client.js";

const CLASSES = [
  "Tomate — mancha bacteriana, tizón, moho, mosca, etc.",
  "Papa — tizón temprano/tardío, sana",
  "Pimiento — mancha bacteriana, sano",
];

export default function Home() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => setHealth({ model_loaded: false }));
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-16">
      <section className="text-center max-w-3xl mx-auto">
        <p className="text-leaf-400 text-sm font-medium tracking-wide uppercase mb-3">
          IA + Agricultura
        </p>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-stone-50 leading-tight">
          Diagnostica enfermedades en hojas con una foto
        </h1>
        <p className="mt-4 text-stone-400 text-base sm:text-lg leading-relaxed">
          Red neuronal convolucional entrenada con PlantVillage. Sube una imagen y obtén la
          enfermedad detectada, confianza y tiempo de inferencia en segundos.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/diagnose"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-leaf-600 hover:bg-leaf-500 font-semibold text-white transition-colors"
          >
            <span>📷</span> Analizar imagen
          </Link>
        </div>

        <div
          className={`mt-6 inline-flex items-center gap-2 text-sm px-4 py-2 rounded-full border ${
            health?.model_loaded
              ? "border-leaf-700/50 bg-leaf-950/40 text-leaf-300"
              : "border-amber-800/50 bg-amber-950/30 text-amber-300"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              health?.model_loaded ? "bg-leaf-400" : "bg-amber-400"
            }`}
          />
          {health?.model_loaded
            ? `Modelo listo · ${health.num_classes} clases${
                health.supabase_configured ? " · Supabase OK" : " · Supabase pendiente"
              }`
            : "Modelo pendiente — ejecuta python ml/train.py"}
        </div>
      </section>

      <section className="mt-16 grid sm:grid-cols-3 gap-4 sm:gap-6">
        {[
          {
            icon: "🔬",
            title: "14 clases",
            desc: "Tomate, papa y pimiento — enfermedades y hojas sanas.",
          },
          {
            icon: "⚡",
            title: "Inferencia rápida",
            desc: "CNN con TensorFlow; modelo guardado en .keras.",
          },
          {
            icon: "☁️",
            title: "Listo para deploy",
            desc: "API FastAPI + frontend Vite preparados para la nube.",
          },
        ].map((card) => (
          <article
            key={card.title}
            className="p-5 sm:p-6 rounded-2xl border border-stone-800 bg-stone-900/50 hover:border-leaf-800/50 transition-colors"
          >
            <div className="text-3xl mb-3">{card.icon}</div>
            <h3 className="font-semibold text-stone-100">{card.title}</h3>
            <p className="mt-2 text-sm text-stone-500 leading-relaxed">{card.desc}</p>
          </article>
        ))}
      </section>

      <section className="mt-12 p-6 rounded-2xl border border-stone-800 bg-gradient-to-r from-stone-900 to-leaf-950/30">
        <h2 className="font-semibold text-stone-200 mb-3">Cultivos soportados</h2>
        <ul className="space-y-2 text-sm text-stone-500">
          {CLASSES.map((item) => (
            <li key={item} className="flex items-start gap-2">
              <span className="text-leaf-500 mt-0.5">✓</span>
              {item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
