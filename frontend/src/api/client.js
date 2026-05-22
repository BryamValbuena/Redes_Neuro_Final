const API_BASE = import.meta.env.VITE_API_URL || "";

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Error al iniciar sesión");
  return data;
}

export async function predictImage(token, file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Error en la predicción");
  return data;
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
