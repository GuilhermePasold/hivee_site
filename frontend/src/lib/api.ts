import type {
  AuthResponse,
  AvailabilitySlot,
  Category,
  City,
  Paginated,
  PlatformStats,
  Provider,
  Recommendation,
  User,
} from "@/types";

const BASE = "/api";

// Smell fix #2: o token NAO fica mais em localStorage (legivel por XSS). Ele
// vive num cookie httpOnly definido pelo servidor; o navegador o envia
// sozinho quando usamos `credentials: "include"`. O JavaScript nunca o ve.

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
  if (opts.body) headers["Content-Type"] = "application/json";

  const res = await fetch(url.toString(), {
    method: opts.method ?? "GET",
    headers,
    credentials: "include", // envia/recebe o cookie httpOnly de autenticacao
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
  city?: string;
  neighborhood?: string;
  state?: string;
  latitude?: number | null;
  longitude?: number | null;
  response_time?: string;
  availability?: string;
  availability_slots?: AvailabilitySlot[];
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
  uploadAvatar: (slug: string, file: File) => {
    const form = new FormData();
    form.append("avatar", file);
    form.append("slug", slug);
    return fetch("/api/upload-avatar/", { method: "POST", body: form, credentials: "include" }).then(
      (r) => r.json() as Promise<{ avatar_url: string }>,
    );
  },

  register: (body: { name: string; email: string; password: string; cpf?: string }) =>
    request<AuthResponse>("/auth/register/", { method: "POST", body }),
  login: (body: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login/", { method: "POST", body }),
  logout: () => request<void>("/auth/logout/", { method: "POST" }),
  me: () => request<User>("/auth/me/"),
};
