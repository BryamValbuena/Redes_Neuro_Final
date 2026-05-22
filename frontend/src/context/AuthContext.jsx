import { createContext, useContext, useMemo, useState } from "react";

const AuthContext = createContext(null);
const STORAGE_KEY = "plantai_token";
const USER_KEY = "plantai_user";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [username, setUsername] = useState(() => localStorage.getItem(USER_KEY));

  const value = useMemo(
    () => ({
      token,
      username,
      isAuthenticated: Boolean(token),
      login: (accessToken, user) => {
        localStorage.setItem(STORAGE_KEY, accessToken);
        localStorage.setItem(USER_KEY, user);
        setToken(accessToken);
        setUsername(user);
      },
      logout: () => {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(USER_KEY);
        setToken(null);
        setUsername(null);
      },
    }),
    [token, username]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
