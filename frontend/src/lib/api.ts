import type {
  AppNotification,
  AuthResponse,
  AvailabilitySlot,
  Category,
  City,
  FAQArticle,
  FeaturedResponse,
  ForYouResponse,
  GalleryImage,
  Paginated,
  PlatformStats,
  Provider,
  Recommendation,
  SupportCategory,
  SupportMessage,
  SupportTicket,
  SwipeAction,
  Tag,
  UnreadCount,
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
  cpf?: string;
}

export interface ProviderUpdateInput {
  headline?: string;
  bio?: string;
  hourly_rate?: number;
  response_time?: string;
  availability?: string;
  city?: string;
  neighborhood?: string;
  state?: string;
  latitude?: number | null;
  longitude?: number | null;
  tags?: string[];
  availability_slots?: AvailabilitySlot[];
}

export const api = {
  categories: () => request<Category[]>("/categories/"),
  cities: () => request<City[]>("/cities/"),
  stats: () => request<PlatformStats>("/stats/"),
  citiesByState: (uf: string) => request<City[]>(`/cities-by-state/${uf}/`),
  tags: (search?: string) =>
    request<Tag[]>("/tags/", { params: search ? { search } : {} }),

  providers: (params: ProviderQuery = {}) =>
    request<Paginated<Provider>>("/providers/", { params: params as Record<string, unknown> }),
  provider: (slug: string, params: { lat?: number; lng?: number } = {}) =>
    request<Provider>(`/providers/${slug}/`, { params }),
  recommended: (params: { lat?: number; lng?: number } = {}) =>
    request<Recommendation[]>("/providers/recommended/", { params }),
  featured: (params: { lat?: number; lng?: number; city?: string } = {}) =>
    request<FeaturedResponse>("/providers/featured/", { params }),

  // --- Match / swipe personalizado (precisa de login) ---
  forYou: (params: { lat?: number; lng?: number } = {}) =>
    request<ForYouResponse>("/providers/for-you/", { params }),
  favorites: (params: { lat?: number; lng?: number } = {}) =>
    request<Provider[]>("/providers/favorites/", { params }),
  swipe: (slug: string, action: SwipeAction, source: "deck" | "profile" = "deck") =>
    request<{ action: SwipeAction; provider: string; remaining_today: number }>(
      `/providers/${slug}/swipe/`,
      { method: "POST", body: { action, source } },
    ),
  unfavorite: (slug: string) =>
    request<void>(`/providers/${slug}/swipe/`, { method: "DELETE" }),
  createProvider: (input: ProviderInput) =>
    request<Provider>("/providers/", { method: "POST", body: input }),
  updateProvider: (slug: string, patch: ProviderUpdateInput) =>
    request<Provider>(`/providers/${slug}/`, { method: "PATCH", body: patch }),
  uploadAvatar: (slug: string, file: File) => {
    const form = new FormData();
    form.append("avatar", file);
    form.append("slug", slug);
    return fetch("/api/upload-avatar/", { method: "POST", body: form, credentials: "include" }).then(
      (r) => r.json() as Promise<{ avatar_url: string }>,
    );
  },
  addGalleryImage: (slug: string, file: File, altText = "") => {
    const form = new FormData();
    form.append("image", file);
    form.append("alt_text", altText);
    return fetch(`/api/providers/${slug}/gallery/`, {
      method: "POST",
      body: form,
      credentials: "include",
    }).then(async (r) => {
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "Falha no upload");
      return r.json() as Promise<GalleryImage>;
    });
  },
  deleteGalleryImage: (slug: string, imageId: number) =>
    request<void>(`/providers/${slug}/gallery/${imageId}/`, { method: "DELETE" }),

  register: (body: { name: string; email: string; password: string; cpf?: string }) =>
    request<AuthResponse>("/auth/register/", { method: "POST", body }),
  login: (body: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login/", { method: "POST", body }),
  logout: () => request<void>("/auth/logout/", { method: "POST" }),
  me: () => request<User>("/auth/me/"),
  updateMe: (patch: { first_name?: string; telefone?: string }) =>
    request<User>("/auth/me/", { method: "PATCH", body: patch }),

  // --- Notificações ---
  notifications: (params: { unread_only?: number; page?: number; page_size?: number } = {}) =>
    request<Paginated<AppNotification>>("/notifications/", { params }),
  notification: (id: number) => request<AppNotification>(`/notifications/${id}/`),
  markNotificationRead: (id: number) =>
    request<void>(`/notifications/${id}/mark_read/`, { method: "POST" }),
  markAllNotificationsRead: () =>
    request<void>("/notifications/mark_all_read/", { method: "POST" }),
  unreadNotificationCount: () => request<UnreadCount>("/notifications/unread_count/"),

  // --- Suporte: Central de Ajuda (FAQ) ---
  faq: (params: { category?: string; search?: string } = {}) =>
    request<FAQArticle[]>("/faq/", { params }),
  faqCategories: () => request<SupportCategory[]>("/faq/categories/"),

  // --- Suporte: Tickets ---
  supportTickets: (params: { status?: string; page?: number; user_id?: number } = {}) =>
    request<Paginated<SupportTicket>>("/support/tickets/", { params }),
  supportTicket: (id: number) => request<SupportTicket>(`/support/tickets/${id}/`),
  createSupportTicket: (body: {
    subject: string;
    description: string;
    category_slug?: string;
    priority?: string;
  }) => request<SupportTicket>("/support/tickets/", { method: "POST", body }),
  sendTicketMessage: (id: number, content: string) =>
    request<SupportMessage>(`/support/tickets/${id}/message/`, {
      method: "POST",
      body: { content },
    }),
  transitionTicket: (id: number, status: string, note?: string) =>
    request<SupportTicket>(`/support/tickets/${id}/transition/`, {
      method: "POST",
      body: { status, note },
    }),
  assignTicket: (id: number, userId: number) =>
    request<SupportTicket>(`/support/tickets/${id}/assign/`, {
      method: "POST",
      body: { user_id: userId },
    }),
  ticketCounts: () => request<Record<string, number>>("/support/tickets/counts/"),
};
