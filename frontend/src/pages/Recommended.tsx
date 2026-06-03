import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ProviderCard from "@/components/ProviderCard";
import type { Recommendation } from "@/types";

const SP = { lat: -23.5613, lng: -46.6565 };

export default function Recommended() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .recommended({ lat: SP.lat, lng: SP.lng })
      .then(setRecs)
      .catch(() => setRecs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-6xl">
        <h1 className="font-display text-5xl font-bold leading-[1.05] sm:text-6xl">
          Os mais <span className="text-gold">indicados</span> agora
        </h1>
        <p className="mt-3 max-w-xl text-muted-foreground">
          Seleção do sistema combinando avaliação, distância, preço e tempo de resposta.
        </p>

        <div className="mt-10">
          {loading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="surface h-80 animate-pulse rounded-3xl opacity-60" />
              ))}
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {recs.map((r) => (
                <div key={r.id} className="flex flex-col gap-2">
                  <ProviderCard provider={r} />
                  <p className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-xs text-foreground/65">
                    {r.match_reason}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
