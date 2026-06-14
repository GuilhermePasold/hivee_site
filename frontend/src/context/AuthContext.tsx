import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { User } from "@/types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, cpf?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // O token vive num cookie httpOnly: nao da pra le-lo aqui. Perguntamos ao
    // servidor quem esta logado; um 401 simplesmente significa "ninguem".
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await api.login({ email, password });
    setUser(res.user);
  }

  async function register(name: string, email: string, password: string, cpf?: string) {
    const res = await api.register({ name, email, password, cpf });
    setUser(res.user);
  }

  async function logout() {
    await api.logout().catch(() => undefined);
    setUser(null);
  }

  return (
    <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
