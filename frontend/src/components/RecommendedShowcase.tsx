import { ArrowRight, BadgeCheck, MapPin, Star } from "lucide-react";
import { Link } from "react-router-dom";
import { BRL } from "@/lib/utils";
import type { Recommendation } from "@/types";

// Liquid-glass showcase: a few REAL glass cards (backdrop-filter) sitting over a
// rich gold/chrome aurora, so the glass refracts the light and glows like the
// references (Mountain Land / liquid-chrome). Contained to one section + a
// handful of cards => no scroll-jank.
const glass =
  "relative overflow-hidden rounded-[1.8rem] border border-white/25 bg-white/[0.1] backdrop-blur-lg " +
  "[box-shadow:inset_2px_2px_2px_rgba(255,255,255,0.5),inset_-2px_-2px_3px_rgba(0,0,0,0.25),0_30px_70px_-30px_rgba(0,0,0,0.9)]";

export default function RecommendedShowcase({ recs }: { recs: Recommendation[] }) {
  const top = recs[0];
  const rest = recs.slice(1, 3);

  return (
    <section id="recomendados" className="px-6 py-16">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2.5rem] border border-white/10 px-6 py-12 sm:px-12 sm:py-16">
        {/* rich aurora backdrop (the "content behind the glass") */}
        <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
          <div
            className="absolute -left-[12%] -top-[30%] h-[80%] w-[55%] rounded-full blur-2xl"
            style={{ background: "radial-gradient(circle, rgba(234,179,8,0.6), transparent 70%)" }}
          />
          <div
            className="absolute -right-[10%] -bottom-[35%] h-[85%] w-[55%] rounded-full blur-2xl"
            style={{ background: "radial-gradient(circle, rgba(202,138,4,0.45), transparent 70%)" }}
          />
          <div
            className="absolute left-[28%] top-[10%] h-[60%] w-[45%] rounded-full blur-2xl"
            style={{ background: "radial-gradient(circle, rgba(253,224,71,0.3), transparent 70%)" }}
          />
          <div
            className="absolute inset-0"
            style={{ background: "linear-gradient(120deg, rgba(255,255,255,0.07), transparent 42%)" }}
          />
          {/* keep text/cards readable over the bright aurora */}
          <div className="absolute inset-0 bg-black/45" />
        </div>

        <div className="relative grid items-center gap-10 lg:grid-cols-2">
          {/* Copy */}
          <div>
            <h2 className="text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-5xl">
              O sistema escolhe.
              <br />
              <span className="text-gold">Você só contrata.</span>
            </h2>
            <p className="mt-5 max-w-md text-foreground/75">
              Nossa recomendação combina avaliação, distância, preço e tempo de resposta para
              colocar o profissional certo na sua frente.
            </p>
            <Link to="/recomendados" className="btn-ghost mt-7 inline-flex px-5 py-3 text-sm">
              Ver todos os recomendados <ArrowRight className="h-4 w-4" />
            </Link>

            {/* small peeking glass cards for depth */}
            {rest.length > 0 && (
              <div className="mt-8 flex gap-3">
                {rest.map((r) => (
                  <Link
                    key={r.id}
                    to={`/prestador/${r.slug}`}
                    className={`${glass} flex flex-1 items-center gap-3 p-3`}
                  >
                    <img src={r.avatar_url} alt={r.name} className="h-10 w-10 rounded-xl object-cover" />
                    <div className="min-w-0">
                      <p className="truncate text-xs font-semibold">{r.name}</p>
                      <p className="flex items-center gap-1 text-[11px] text-gold-300">
                        <Star className="h-3 w-3 fill-gold-400 text-gold-400" />
                        {r.rating.toFixed(1)}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Featured glass card */}
          {top && (
            <Link to={`/prestador/${top.slug}`} className={`${glass} group block p-6 sm:p-7`}>
              <span className="inline-flex items-center rounded-full border border-gold-400/40 bg-black/40 px-3 py-1 text-[11px] font-semibold text-gold-200">
                {top.match_score}% match
              </span>
              <div className="mt-4 flex items-center gap-4">
                <img
                  src={top.avatar_url}
                  alt={top.name}
                  className="h-20 w-20 rounded-2xl border-2 border-white/30 object-cover"
                />
                <div>
                  <p className="flex items-center gap-1.5 text-2xl font-bold">
                    {top.name}
                    {top.verified && <BadgeCheck className="h-5 w-5 text-gold-300" />}
                  </p>
                  <p className="text-sm text-foreground/75">{top.headline}</p>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-4 text-sm text-foreground/80">
                <span className="flex items-center gap-1">
                  <Star className="h-4 w-4 fill-gold-400 text-gold-400" />
                  <b>{top.rating.toFixed(1)}</b> ({top.reviews_count})
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="h-4 w-4 text-gold-300" /> {top.neighborhood}
                </span>
              </div>
              <p className="mt-4 rounded-2xl border border-white/15 bg-white/[0.06] p-3 text-sm leading-relaxed text-foreground/85">
                {top.match_reason}
              </p>
              <div className="mt-5 flex items-center justify-between border-t border-white/15 pt-4">
                <span className="text-xl font-bold">
                  {BRL.format(top.hourly_rate)}
                  <span className="text-sm font-normal text-foreground/60">/h</span>
                </span>
                <span className="btn-gold px-5 py-2.5 text-sm transition-transform group-hover:translate-x-0.5">
                  Ver perfil <ArrowRight className="h-4 w-4" />
                </span>
              </div>
            </Link>
          )}
        </div>
      </div>
    </section>
  );
}
