import { Instagram, Linkedin, Twitter, ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CinematicHero } from "@/components/ui/cinematic-landing-hero";
import { MinimalistHero } from "@/components/ui/minimalist-hero";
import { StackedCardsInteraction } from "@/components/ui/stacked-cards-interaction";
import Icon from "@/components/ui/Icon";
import PhoneApp from "@/components/PhoneApp";
import RecCard from "@/components/RecCard";
import { api } from "@/lib/api";
import { getUserLocation } from "@/lib/location";
import type { Category, PlatformStats, Recommendation } from "@/types";

export default function Home() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);

  useEffect(() => {
    api.stats().then(setStats).catch(() => undefined);
    api.categories().then(setCategories).catch(() => undefined);
    // Usa a localizacao real do usuario (com fallback configuravel).
    getUserLocation().then((loc) =>
      api.recommended(loc).then(setRecs).catch(() => undefined),
    );
  }, []);

  return (
    <div>
      {/* Cinematic intro */}
      <CinematicHero
        metricValue={stats?.providers ?? 180}
        onPrimary={() => navigate("/buscar")}
        onSecondary={() => navigate("/sou-prestador")}
      />

      {/* 2 — The site hero */}
      <MinimalistHero
        logo={<img src="/hivee_logo.png" alt="HIVEE" className="h-16 w-auto" />}
        navLinks={[]}
        mainText="A HIVEE conecta você aos melhores prestadores de serviço perto de você. Compare avaliações, preços e distância e contrate em minutos."
        ctaLabel="Buscar profissionais"
        onCta={() => navigate("/buscar")}
        imageSrc="/shot-busca.png"
        imageAlt="App HIVEE: busca de profissionais"
        phoneContent={<PhoneApp />}
        overlayText={{ part1: "Achou.", part2: "Contratou." }}
        socialLinks={[
          { icon: Instagram, href: "#" },
          { icon: Twitter, href: "#" },
          { icon: Linkedin, href: "#" },
        ]}
        locationText={`Brasil · ${stats?.cities ?? 12} cidades`}
      />

      {/* 3 — Categories */}
      <section className="px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <SectionHeader title={<>Todo serviço que você imagina,<br /><span className="text-gold">em um só lugar.</span></>} />
          <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {categories.map((c, i) => (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.5, delay: (i % 4) * 0.06, ease: [0.16, 1, 0.3, 1] }}
              >
                <Link
                  to={`/buscar?categoria=${c.slug}`}
                  className="surface card-hover flex h-full flex-col items-start gap-4 rounded-3xl p-5"
                >
                  <span
                    className="flex h-12 w-12 items-center justify-center rounded-2xl"
                    style={{ background: `linear-gradient(135deg, ${c.accent}40, transparent)`, border: `1px solid ${c.accent}40` }}
                  >
                    <Icon name={c.icon} className="h-6 w-6 text-gold-300" />
                  </span>
                  <div>
                    <h3 className="font-display text-lg font-semibold">{c.name}</h3>
                    <p className="mt-0.5 text-xs text-muted-foreground">{c.tagline}</p>
                  </div>
                  <span className="mt-auto text-[11px] text-muted-foreground">{c.provider_count} profissionais</span>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 4 — Recommended (swipe deck) */}
      <section className="px-6 py-12">
        <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-2">
          <div>
            <SectionHeader title={<>O sistema escolhe.<br /><span className="text-gold">Você só contrata.</span></>} />
            <p className="mt-5 max-w-md text-muted-foreground">
              Nossa recomendação combina avaliação, distância, preço e tempo de resposta para
              colocar o profissional certo na sua frente. Passe o mouse para abrir o leque.
            </p>
            <Link to="/recomendados" className="btn-ghost mt-7 inline-flex px-5 py-3 text-sm">
              Ver todos os recomendados <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="flex h-[460px] items-center justify-center">
            {recs.length > 0 && (
              <StackedCardsInteraction
                cards={recs.slice(0, 3).map((r) => (
                  <Link key={r.id} to={`/prestador/${r.slug}`} className="block h-full">
                    <RecCard rec={r} />
                  </Link>
                ))}
              />
            )}
          </div>
        </div>
      </section>

      {/* 6 — CTA */}
      <section className="px-6 py-12">
        <div className="surface mx-auto max-w-5xl overflow-hidden rounded-[2rem] p-10 text-center sm:p-16">
          <h2 className="mx-auto max-w-3xl font-display text-4xl font-bold sm:text-6xl">
            Tem um talento? <span className="text-gold">O enxame precisa de você.</span>
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-muted-foreground">
            Crie seu perfil, apareça para milhares de clientes na sua região e receba só os
            pedidos que combinam com você. Sem mensalidade.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/sou-prestador" className="btn-gold px-7 py-3.5 text-base">
              Quero me cadastrar <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/buscar" className="btn-ghost px-7 py-3.5 text-base">
              Buscar profissionais
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function SectionHeader({ title }: { title: React.ReactNode }) {
  return (
    <div className="max-w-2xl">
      <h2 className="font-display text-4xl font-bold leading-[1.05] sm:text-5xl">{title}</h2>
    </div>
  );
}
