import { BadgeCheck, MapPin, Star, Clock } from "lucide-react";
import { Link } from "react-router-dom";
import type { Provider } from "@/types";
import { BRL } from "@/lib/utils";
import Icon from "@/components/ui/Icon";
import Avatar from "@/components/ui/Avatar";

export default function ProviderCard({ provider }: { provider: Provider }) {
  const accent = provider.category.accent || "#eab308";
  return (
    <Link
      to={`/prestador/${provider.slug}`}
      className="surface card-hover group flex h-full flex-col overflow-hidden rounded-3xl"
    >
      <div
        className="relative h-20 w-full"
        style={{ background: `linear-gradient(135deg, ${accent}33, transparent 60%)` }}
      >
        <span className="absolute right-3 top-3 flex items-center gap-1.5 rounded-full border border-white/15 bg-black/55 px-2.5 py-1 text-[11px] text-foreground/85">
          <Icon name={provider.category.icon} className="h-3 w-3 text-gold-400" />
          {provider.category.name}
        </span>
        <Avatar
          src={provider.avatar || provider.avatar_url}
          alt={provider.name}
          size={64}
          className="absolute -bottom-7 left-5 rounded-2xl border-2 border-white/20 object-cover"
        />
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5 pt-9">
        <div>
          <div className="flex items-center gap-1.5">
            <h3 className="font-display text-lg font-semibold">{provider.name}</h3>
            {provider.verified && <BadgeCheck className="h-4 w-4 text-gold-400" />}
          </div>
          <p className="text-sm text-muted-foreground">{provider.headline}</p>
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-foreground/70">
          <span className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 fill-gold-400 text-gold-400" />
            <span className="font-semibold text-foreground">{provider.rating.toFixed(1)}</span>
            <span className="text-muted-foreground">({provider.reviews_count})</span>
          </span>
          <span className="flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5 text-gold-400" />
            {provider.neighborhood || provider.city || "Sem endereço"}
            {provider.distance_km != null && (
              <span className="text-gold-300">· {provider.distance_km.toFixed(1)} km</span>
            )}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5 text-gold-400" />
            {provider.response_time}
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {provider.skills.slice(0, 3).map((s) => (
            <span key={s} className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-foreground/70">
              {s}
            </span>
          ))}
        </div>

        <div className="mt-auto flex items-center justify-between border-t border-white/10 pt-4">
          <div>
            <p className="text-base font-semibold">
              {BRL.format(provider.hourly_rate)}
              <span className="text-xs font-normal text-muted-foreground">/h</span>
            </p>
            <p className="text-[11px] text-muted-foreground">{provider.jobs_done} serviços</p>
          </div>
          <span className="btn-gold px-4 py-2 text-sm transition-transform group-hover:translate-x-0.5">
            Ver perfil
          </span>
        </div>
      </div>
    </Link>
  );
}
