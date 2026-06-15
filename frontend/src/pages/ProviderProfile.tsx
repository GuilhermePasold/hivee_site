import L from "leaflet";
import { MapContainer, Marker, TileLayer } from "react-leaflet";
import {
  ArrowLeft, BadgeCheck, Clock, MapPin, MessageSquare, Phone,
  Star, CalendarCheck, Award,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { BRL } from "@/lib/utils";
import Avatar from "@/components/ui/Avatar";
import Icon from "@/components/ui/Icon";
import type { Provider } from "@/types";

const pin = (avatar: string) =>
  L.divIcon({
    className: "",
    iconSize: [50, 50],
    iconAnchor: [25, 50],
    html: `<div style="width:46px;height:46px;border-radius:50%;padding:2px;background:linear-gradient(135deg,#facc15,#ca8a04);box-shadow:0 8px 20px -6px rgba(0,0,0,.7)">
      <img src="${avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;border:2px solid #09090b"/></div>`,
  });

export default function ProviderProfile() {
  const { slug } = useParams<{ slug: string }>();
  const [p, setP] = useState<Provider | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(false);
    api
      .provider(slug)
      .then(setP)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen px-6 pt-28">
        <div className="mx-auto max-w-5xl">
          <div className="surface h-48 animate-pulse rounded-3xl" />
          <div className="surface mt-6 h-64 animate-pulse rounded-3xl opacity-60" />
        </div>
      </div>
    );
  }

  if (error || !p) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="font-display text-3xl font-bold">Profissional não encontrado</p>
        <Link to="/buscar" className="btn-gold px-6 py-3">Voltar para a busca</Link>
      </div>
    );
  }

  const accent = p.category.accent || "#eab308";
  const stats = [
    { icon: Star, label: "Avaliação", value: `${p.rating.toFixed(1)} (${p.reviews_count})` },
    { icon: CalendarCheck, label: "Serviços", value: String(p.jobs_done) },
    { icon: Clock, label: "Resposta", value: p.response_time },
    { icon: Award, label: "Na HIVEE desde", value: String(p.member_since) },
  ];

  return (
    <div className="min-h-screen px-6 pb-24 pt-24">
      <div className="mx-auto max-w-5xl">
        <Link to="/buscar" className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Voltar para a busca
        </Link>

        {/* Cover + identity */}
        <div className="surface relative overflow-hidden rounded-[2rem]">
          <div className="h-40 w-full" style={{ background: `linear-gradient(135deg, ${accent}66, transparent 70%)` }} />
          <div className="flex flex-col gap-5 p-6 sm:flex-row sm:items-end sm:gap-6 sm:p-8">
            <Avatar
              src={p.avatar || p.avatar_url}
              alt={p.name}
              size={112}
              className="-mt-20 rounded-3xl border-2 border-white/20 object-cover shadow-xl"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h1 className="font-display text-3xl font-bold sm:text-4xl">{p.name}</h1>
                {p.status === "approved" && <BadgeCheck className="h-6 w-6 text-gold-400" />}
                {p.status === "pending" && <span className="rounded-full border border-yellow-500/40 bg-yellow-500/10 px-2.5 py-0.5 text-xs font-medium text-yellow-400">Em análise</span>}
                {p.status === "rejected" && <span className="rounded-full border border-rose-500/40 bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400">Rejeitado</span>}
              </div>
              <p className="mt-1 text-lg text-muted-foreground">{p.headline}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-foreground/75">
                <span className="flex items-center gap-1.5">
                  <Icon name={p.category.icon} className="h-4 w-4 text-gold-400" /> {p.category.name}
                </span>
                {p.latitude && p.longitude ? (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="h-4 w-4 text-gold-400" /> {p.neighborhood}, {p.city} - {p.state}
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-muted-foreground/50 italic">
                    <MapPin className="h-4 w-4 text-muted-foreground/50" /> Sem endereço cadastrado
                  </span>
                )}
                <span className="flex items-center gap-1.5 text-gold-300">{p.availability}</span>
              </div>
            </div>
            <div className="text-right">
              <p className="font-display text-3xl font-bold">{BRL.format(p.hourly_rate)}<span className="text-base font-normal text-muted-foreground">/h</span></p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="surface rounded-2xl p-5">
              <s.icon className="h-5 w-5 text-gold-400" />
              <p className="mt-3 font-display text-xl font-semibold">{s.value}</p>
              <p className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          {/* Bio + skills */}
          <div className="surface rounded-3xl p-6 sm:p-8">
            <h2 className="font-display text-2xl font-semibold">Sobre</h2>
            <p className="mt-3 leading-relaxed text-foreground/80">{p.bio}</p>

            <h3 className="mt-8 font-display text-lg font-semibold">Especialidades</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {p.skills.map((s) => (
                <span key={s} className="rounded-full border border-white/12 bg-white/5 px-3.5 py-1.5 text-sm text-foreground/80">
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Map + contact */}
          <div className="flex flex-col gap-6">
            {p.latitude && p.longitude ? (
              <div className="surface overflow-hidden rounded-3xl p-1.5">
                <div className="h-56 overflow-hidden rounded-[1.4rem]">
                  <MapContainer
                    center={[p.latitude, p.longitude]}
                    zoom={13}
                    scrollWheelZoom={false}
                    style={{ height: "100%", width: "100%" }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={[p.latitude, p.longitude]} icon={pin(p.avatar || p.avatar_url)} />
                  </MapContainer>
                </div>
              </div>
            ) : (
              <div className="surface flex h-56 items-center justify-center rounded-3xl">
                <p className="text-sm italic text-muted-foreground/50">Sem endereço cadastrado</p>
              </div>
            )}

            <div className="surface flex flex-col gap-3 rounded-3xl p-6">
              <button className="btn-gold w-full py-3.5 text-base">
                <MessageSquare className="h-4 w-4" /> Enviar mensagem
              </button>
              <button className="btn-ghost w-full py-3.5 text-base">
                <Phone className="h-4 w-4" /> Solicitar orçamento
              </button>
              <p className="text-center text-xs text-muted-foreground">
                Pagamento protegido pela HIVEE · garantia de satisfação
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
