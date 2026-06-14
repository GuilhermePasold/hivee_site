// Smell fix #5: coordenadas que antes estavam "chumbadas" dentro das paginas
// agora moram num unico lugar e sao configuraveis por variavel de ambiente
// (Vite). A Home tenta primeiro a localizacao REAL do usuario e so cai no
// padrao quando ela nao esta disponivel.

export interface LatLng {
  lat: number;
  lng: number;
}

// Padrao usado apenas como ultimo recurso (ex.: usuario nega a geolocalizacao).
export const DEFAULT_LOCATION: LatLng = {
  lat: Number(import.meta.env.VITE_DEFAULT_LAT ?? -23.5613),
  lng: Number(import.meta.env.VITE_DEFAULT_LNG ?? -46.6565),
};

/** Resolve a localizacao real do navegador, com fallback para o padrao. */
export function getUserLocation(): Promise<LatLng> {
  return new Promise((resolve) => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      resolve(DEFAULT_LOCATION);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(DEFAULT_LOCATION),
      { timeout: 5000, maximumAge: 600000 },
    );
  });
}
