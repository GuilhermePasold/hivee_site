import {
  ChevronDown,
  CreditCard,
  HelpCircle,
  LifeBuoy,
  MessageCircle,
  Plus,
  Search,
  ShieldCheck,
  Ticket,
  UserCircle,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useChat } from "@/context/ChatContext";
import { api } from "@/lib/api";
import type { FAQArticle, SupportCategory } from "@/types";

const ICONS: Record<string, LucideIcon> = {
  UserCircle,
  Wrench,
  CreditCard,
  ShieldCheck,
  MessageCircle,
  LifeBuoy,
  HelpCircle,
};

function CategoryIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICONS[name] || HelpCircle;
  return <Icon className={className} />;
}

export default function Ajuda() {
  const { openChat } = useChat();
  const [categories, setCategories] = useState<SupportCategory[]>([]);
  const [articles, setArticles] = useState<FAQArticle[]>([]);
  const [activeCat, setActiveCat] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    api.faqCategories().then(setCategories).catch(() => undefined);
  }, []);

  useEffect(() => {
    let active = true;
    setBusy(true);
    const params: { category?: string; search?: string } = {};
    if (activeCat) params.category = activeCat;
    if (search.trim()) params.search = search.trim();
    const t = setTimeout(() => {
      api
        .faq(params)
        .then((a) => active && setArticles(a))
        .catch(() => undefined)
        .finally(() => active && setBusy(false));
    }, 250);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [activeCat, search]);

  const activeCategoryName = useMemo(
    () => categories.find((c) => c.slug === activeCat)?.name,
    [categories, activeCat],
  );

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center gap-3">
          <LifeBuoy className="h-8 w-8 text-gold-400" />
          <h1 className="font-display text-4xl font-extrabold tracking-tight sm:text-5xl">
            Central de <span className="text-gold">Ajuda</span>
          </h1>
        </div>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Encontre respostas rápidas. Não achou o que procurava? Abra um ticket ou fale com a gente no chat.
        </p>

        {/* Busca */}
        <div className="mt-8 flex items-center gap-3 rounded-2xl border border-white/12 bg-white/5 px-4 py-3 focus-within:border-gold-500/50">
          <Search className="h-5 w-5 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar dúvidas (ex.: pagamento, cadastro, perfil)"
            className="min-w-0 flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
        </div>

        {/* Categorias */}
        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <CatChip
            active={activeCat === null}
            onClick={() => setActiveCat(null)}
            icon={<HelpCircle className="h-5 w-5" />}
            label="Todas"
          />
          {categories.map((c) => (
            <CatChip
              key={c.slug}
              active={activeCat === c.slug}
              onClick={() => setActiveCat(activeCat === c.slug ? null : c.slug)}
              icon={<CategoryIcon name={c.icon} className="h-5 w-5" />}
              label={c.name}
              count={c.article_count}
            />
          ))}
        </div>

        {/* Artigos */}
        <section className="mt-10">
          <h2 className="font-display text-2xl font-semibold">
            {activeCategoryName || (search ? "Resultados" : "Perguntas frequentes")}
          </h2>

          <div className="mt-5 space-y-3">
            {busy ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="surface h-16 animate-pulse rounded-2xl opacity-60" />
              ))
            ) : articles.length === 0 ? (
              <div className="surface rounded-3xl p-10 text-center">
                <HelpCircle className="mx-auto h-8 w-8 text-gold-400" />
                <p className="mt-3 font-display text-xl font-semibold">Nada encontrado</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Tente outra busca ou abra um ticket — nossa equipe ajuda você.
                </p>
              </div>
            ) : (
              articles.map((a) => (
                <article key={a.id} className="surface overflow-hidden rounded-2xl">
                  <button
                    type="button"
                    onClick={() => setOpenId(openId === a.id ? null : a.id)}
                    className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                  >
                    <span className="font-medium">{a.question}</span>
                    <ChevronDown
                      className={`h-5 w-5 flex-none text-gold-400 transition-transform ${openId === a.id ? "rotate-180" : ""}`}
                    />
                  </button>
                  {openId === a.id && (
                    <div className="border-t border-white/8 px-5 py-4 text-sm leading-relaxed text-foreground/80">
                      <p className="whitespace-pre-wrap">{a.answer}</p>
                      <Link
                        to={`/ajuda/${a.slug}`}
                        className="mt-3 inline-flex text-sm text-gold-300 hover:underline"
                      >
                        Abrir página do artigo →
                      </Link>
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </section>

        {/* CTAs */}
        <section className="mt-12 grid gap-4 sm:grid-cols-3">
          <Link to="/suporte/novo" className="surface card-hover flex flex-col gap-2 rounded-3xl p-6">
            <Plus className="h-6 w-6 text-gold-400" />
            <span className="font-semibold">Abrir um ticket</span>
            <span className="text-sm text-muted-foreground">Fale com nossa equipe de suporte.</span>
          </Link>
          <Link to="/suporte/tickets" className="surface card-hover flex flex-col gap-2 rounded-3xl p-6">
            <Ticket className="h-6 w-6 text-gold-400" />
            <span className="font-semibold">Meus tickets</span>
            <span className="text-sm text-muted-foreground">Acompanhe suas solicitações.</span>
          </Link>
          <button
            type="button"
            onClick={() => openChat()}
            className="surface card-hover flex flex-col gap-2 rounded-3xl p-6 text-left"
          >
            <MessageCircle className="h-6 w-6 text-gold-400" />
            <span className="font-semibold">Falar no chat</span>
            <span className="text-sm text-muted-foreground">Tire dúvidas com a assistente Vee.</span>
          </button>
        </section>
      </div>
    </div>
  );
}

function CatChip({
  active,
  onClick,
  icon,
  label,
  count,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  count?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-left transition-colors ${
        active
          ? "border-gold-500/50 bg-gold-500/15 text-gold-100"
          : "border-white/12 bg-white/5 text-foreground/80 hover:border-gold-500/30 hover:text-foreground"
      }`}
    >
      <span className={active ? "text-gold-300" : "text-gold-400"}>{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{label}</span>
        {typeof count === "number" && (
          <span className="block text-xs text-muted-foreground">{count} artigo{count === 1 ? "" : "s"}</span>
        )}
      </span>
    </button>
  );
}
