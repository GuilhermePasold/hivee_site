import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { getUserLocation } from "@/lib/location";
import ProviderCard from "@/components/ProviderCard";
import type { FeaturedResponse, Provider } from "@/types";

export default function Recommended() {
  const [prestadores, setPrestadores] = useState<Provider[]>([]);
  const [fallback, setFallback] = useState(false);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUserLocation().then((loc) =>
      api
        .featured({ lat: loc.lat, lng: loc.lng })
        .then((res: FeaturedResponse) => {
          setPrestadores(res.prestadores);
          setFallback(res.fallback);
          setMensagem(res.mensagem);
        })
        .catch(() => {
          setPrestadores([]);
          setFallback(true);
          setMensagem("Nenhum prestador em destaque encontrado na sua região.");
        })
        .finally(() => setLoading(false)),
    );
  }, []);

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-6xl">
        <h1 className="font-display text-5xl font-bold leading-[1.05] sm:text-6xl">
          Os mais <span className="text-gold">indicados</span> agora
        </h1>
        <p className="mt-3 max-w-xl text-muted-foreground">
          Prestadores em destaque perto de você — ordenados por serviços realizados e avaliação.
        </p>

        <div className="mt-10">
          {loading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="surface h-80 animate-pulse rounded-3xl opacity-60" />
              ))}
            </div>
          ) : fallback || prestadores.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-24 text-center">
              <div className="text-5xl opacity-30">📍</div>
              <p className="max-w-md text-muted-foreground">
                {mensagem ?? "Nenhum prestador em destaque encontrado na sua região."}
              </p>
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {prestadores.map((p) => (
                <ProviderCard key={p.id} provider={p} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
