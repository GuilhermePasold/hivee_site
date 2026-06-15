export interface Category {
  id: number;
  slug: string;
  name: string;
  icon: string;
  tagline: string;
  accent: string;
  provider_count: number;
}

export interface AvailabilitySlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface Provider {
  id: number;
  slug: string;
  name: string;
  headline: string;
  bio: string;
  category: Category;
  avatar_url: string;
  avatar?: string | null;
  cover_url: string;
  rating: number;
  reviews_count: number;
  jobs_done: number;
  hourly_rate: number;
  currency: string;
  city?: string;
  neighborhood?: string;
  state?: string;
  latitude?: number | null;
  longitude?: number | null;
  distance_km: number | null;
  verified: boolean;
  top_rated: boolean;
  response_time: string;
  availability: string;
  availability_slots?: AvailabilitySlot[];
  skills: string[];
  member_since: number;
  status: "pending" | "approved" | "rejected";
  is_favorited?: boolean;
  tags?: Tag[];
  gallery?: GalleryImage[];
  profile_completeness?: number;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
  provider_count?: number;
}

export interface GalleryImage {
  id: number;
  image_url: string | null;
  alt_text: string;
  created_at: string;
}

export interface Recommendation extends Provider {
  match_score: number;
  match_reason: string;
}

export type SwipeAction = "like" | "dislike";

export interface ForYouResponse {
  results: Recommendation[];
  daily_limit: number;
  remaining_today: number;
  has_searched: boolean;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PlatformStats {
  providers: number;
  categories: number;
  cities: number;
  avg_rating: number;
  jobs_done: number;
}

export interface City {
  city: string;
  state: string;
  count: number;
}

export interface GeoPoint {
  lat: number;
  lng: number;
  label: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  is_provider: boolean;
  provider_slug: string | null;
  cpf?: string | null;
  telefone?: string;
  provider_status?: "" | "pending" | "approved" | "rejected";
  is_staff?: boolean;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export type NotificationTipo =
  | "provider_approved"
  | "provider_rejected"
  | "cpf_verified"
  | "cpf_mismatch"
  | "order_requested"
  | "order_confirmed"
  | "order_in_progress"
  | "order_completed"
  | "order_cancelled"
  | "order_disputed"
  | "order_reviewed"
  | "new_message"
  | "new_provider_in_area"
  | "recommendation";

export interface AppNotification {
  id: number;
  tipo: NotificationTipo;
  title: string;
  body: string;
  link: string;
  payload: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}

export interface FeaturedResponse {
  prestadores: Provider[];
  total: number;
  fallback: boolean;
  mensagem: string | null;
}

// --- Suporte ao usuário ----------------------------------------------------
export type SupportTicketStatus =
  | "open"
  | "waiting_user"
  | "waiting_staff"
  | "resolved"
  | "closed";

export type SupportTicketPriority = "low" | "medium" | "high" | "urgent";

export interface SupportCategory {
  id: number;
  slug: string;
  name: string;
  icon: string;
  order: number;
  article_count?: number;
}

export interface FAQArticle {
  id: number;
  category: SupportCategory | null;
  question: string;
  slug: string;
  answer: string;
  order: number;
}

export interface SupportMessage {
  id: number;
  author_name: string;
  content: string;
  is_staff: boolean;
  attachment: string | null;
  created_at: string;
}

export interface SupportTicketLog {
  id: number;
  from_status: string;
  to_status: string;
  changed_by_name: string;
  note: string;
  created_at: string;
}

export interface SupportTicket {
  id: number;
  user_name: string;
  category: SupportCategory | null;
  subject: string;
  description: string;
  status: SupportTicketStatus;
  priority: SupportTicketPriority;
  assigned_to: number | null;
  assigned_to_name: string | null;
  messages: SupportMessage[];
  logs: SupportTicketLog[];
  can_transition: SupportTicketStatus[];
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
}
