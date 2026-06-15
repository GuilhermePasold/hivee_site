import { Star, MapPin } from "lucide-react";
import { BRL } from "@/lib/utils";
import Avatar from "@/components/ui/Avatar";
import type { Recommendation } from "@/types";

// Conteúdo visual do card de recomendação (sem navegação própria), para ser
// reaproveitado pela Home (dentro de um <Link>) e pelo deck de swipe (dentro de
// um cartão arrastável). Mantém exatamente o visual original da Home.
export default function RecCard({ rec }: { rec: Recommendation }) {
  return (
    <div className="flex h-full flex-col">
      <div className="relative h-40 w-full shrink-0 bg-gradient-to-br from-white/[0.12] via-white/[0.04] to-transparent">
        <span className="absolute left-4 top-4 inline-flex items-center rounded-full border border-gold-500/30 bg-black/60 px-3 py-1 text-[11px] font-semibold text-gold-300">
          {rec.match_score}% match
        </span>
        <Avatar src={rec.avatar || rec.avatar_url} alt={rec.name} size={80} className="absolute -bottom-8 left-6 rounded-2xl border-2 border-white/20 object-cover" />
      </div>
      <div className="flex flex-1 flex-col gap-3 p-6 pt-11">
        <div>
          <h3 className="font-display text-xl font-semibold">{rec.name}</h3>
          <p className="text-sm text-muted-foreground">{rec.headline}</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-foreground/70">
          <span className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 fill-gold-400 text-gold-400" />
            <span className="font-semibold text-foreground">{rec.rating.toFixed(1)}</span>
          </span>
          <span className="flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5 text-gold-400" /> {rec.neighborhood || rec.city || "Sem endereço"}
          </span>
        </div>
        <p className="line-clamp-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs leading-relaxed text-foreground/65">
          {rec.match_reason}
        </p>
        <div className="mt-auto flex items-center justify-between border-t border-white/10 pt-3">
          <span className="font-semibold">{BRL.format(rec.hourly_rate)}<span className="text-xs font-normal text-muted-foreground">/h</span></span>
          <span className="text-xs text-gold-300">Ver perfil →</span>
        </div>
      </div>
    </div>
  );
}
