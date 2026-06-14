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
}

export interface Recommendation extends Provider {
  match_score: number;
  match_reason: string;
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
}

export interface AuthResponse {
  token: string;
  user: User;
}
