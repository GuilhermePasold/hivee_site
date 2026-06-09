import type {
  AuthResponse,
  Category,
  City,
  Paginated,
  PlatformStats,
  Provider,
  Recommendation,
  User,
} from "@/types";

const BASE = "/api";
const TOKEN_KEY = "hivee_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY); // Code smell: Armazenamento inseguro de credencial (Security Smell); manter token de autenticacao em localStorage facilita roubo por XSS, pois qualquer script executado na pagina pode ler o token e reutiliza-lo como se fosse o usuario.
  } catch {
    return null;
  }
}
export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

async function request<T>(
  path: string,
  opts: { params?: Record<string, unknown>; method?: string; body?: unknown } = {},
): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (opts.params) {
    for (const [k, v] of Object.entries(opts.params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Token ${token}`;
  if (opts.body) headers["Content-Type"] = "application/json";

  const res = await fetch(url.toString(), {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let detail = `HIVEE API ${res.status}`;
    try {
      const data = await res.json();
      detail = data.detail || Object.values(data).flat().join(" ") || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface ProviderQuery {
  category?: string;
  city?: string;
  search?: string;
  lat?: number;
  lng?: number;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface ProviderInput {
  name: string;
  headline: string;
  bio: string;
  category: string;
  avatar_url?: string;
  hourly_rate: number;
  city: string;
  neighborhood: string;
  state: string;
  latitude: number;
  longitude: number;
  response_time: string;
  availability: string;
  skills: string[];
}

export const api = {
  categories: () => request<Category[]>("/categories/"),
  cities: () => request<City[]>("/cities/"),
  stats: () => request<PlatformStats>("/stats/"),

  providers: (params: ProviderQuery = {}) =>
    request<Paginated<Provider>>("/providers/", { params: params as Record<string, unknown> }),
  provider: (slug: string, params: { lat?: number; lng?: number } = {}) =>
    request<Provider>(`/providers/${slug}/`, { params }),
  recommended: (params: { lat?: number; lng?: number } = {}) =>
    request<Recommendation[]>("/providers/recommended/", { params }),
  createProvider: (input: ProviderInput) =>
    request<Provider>("/providers/", { method: "POST", body: input }),

  register: (body: { name: string; email: string; password: string }) =>
    request<AuthResponse>("/auth/register/", { method: "POST", body }),
  login: (body: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login/", { method: "POST", body }),
  me: () => request<User>("/auth/me/"),
};
