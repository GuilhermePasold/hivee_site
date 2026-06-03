import type { GeoPoint } from "@/types";

const NOMINATIM = "https://nominatim.openstreetmap.org";

export interface GeoSuggestion extends GeoPoint {
  id: string;
  city: string;
}

export async function searchAddress(query: string): Promise<GeoSuggestion[]> {
  if (query.trim().length < 3) return [];
  const url = new URL(`${NOMINATIM}/search`);
  url.searchParams.set("q", query);
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("addressdetails", "1");
  url.searchParams.set("limit", "5");
  url.searchParams.set("countrycodes", "br");
  url.searchParams.set("accept-language", "pt-BR");

  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) return [];
  const data = (await res.json()) as Array<{
    place_id: number;
    lat: string;
    lon: string;
    display_name: string;
    address?: Record<string, string>;
  }>;
  return data.map((d) => {
    const a = d.address ?? {};
    const city = a.city || a.town || a.village || a.municipality || a.county || "";
    return {
      id: String(d.place_id),
      lat: parseFloat(d.lat),
      lng: parseFloat(d.lon),
      city,
      label: shorten(d.display_name),
    };
  });
}

export async function reverseGeocode(lat: number, lng: number): Promise<GeoSuggestion> {
  const url = new URL(`${NOMINATIM}/reverse`);
  url.searchParams.set("lat", String(lat));
  url.searchParams.set("lon", String(lng));
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("accept-language", "pt-BR");
  try {
    const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
    const d = (await res.json()) as { display_name?: string; address?: Record<string, string> };
    const a = d.address ?? {};
    const city = a.city || a.town || a.village || a.municipality || a.county || "";
    return { id: "me", lat, lng, city, label: city || (d.display_name ? shorten(d.display_name) : "Minha localização") };
  } catch {
    return { id: "me", lat, lng, city: "", label: "Minha localização" };
  }
}

export function getBrowserLocation(): Promise<GeoSuggestion> {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Geolocalização não suportada"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => resolve(await reverseGeocode(pos.coords.latitude, pos.coords.longitude)),
      (err) => reject(err),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  });
}

function shorten(displayName: string): string {
  const parts = displayName.split(",").map((p) => p.trim());
  if (parts.length <= 3) return displayName;
  return [parts[0], parts[parts.length - 4] ?? parts[1], parts[parts.length - 3] ?? ""]
    .filter(Boolean)
    .join(", ");
}
