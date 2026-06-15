import { useEffect, useState } from "react";
import { Activity, BadgeCheck, CalendarClock, Handshake, Heart, Loader2, LogOut, Mail, Pencil, Phone, Search, Trash2, User as UserIcon, Wrench } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { getUserLocation } from "@/lib/location";
import SwipeDeck from "@/components/SwipeDeck";
import ProviderCard from "@/components/ProviderCard";
import type { Provider, Recommendation, SwipeAction } from "@/types";

type Tab = "para-voce" | "favoritos";

export default function MinhaConta() {
  const { user, loading, logout, refresh } = useAuth();
  const navigate = useNavigate();

  const [editing, setEditing] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [phoneInput, setPhoneInput] = useState("");
  const [savingMe, setSavingMe] = useState(false);
  const [meError, setMeError] = useState("");

  const [tab, setTab] = useState<Tab>("para-voce");
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [dailyLimit, setDailyLimit] = useState(5);
  const [remaining, setRemaining] = useState(0);
  const [hasSearched, setHasSearched] = useState(true);
  const [favorites, setFavorites] = useState<Provider[]>([]);
  const [deckLoading, setDeckLoading] = useState(true);
  const [favLoading, setFavLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    let active = true;
    setDeckLoading(true);
    setFavLoading(true);
    getUserLocation().then((loc) => {
      api
        .forYou(loc)
        .then((r) => {
          if (!active) return;
          setRecs(r.results);
          setDailyLimit(r.daily_limit);
          setRemaining(r.remaining_today);
          setHasSearched(r.has_searched);
        })
        .catch(() => undefined)
        .finally(() => active && setDeckLoading(false));
      api
        .favorites(loc)
        .then((f) => active && setFavorites(f))
        .catch(() => undefined)
        .finally(() => active && setFavLoading(false));
    });
    return () => {
      active = false;
    };
  }, [user]);

  function handleSwipe(rec: Recommendation, action: SwipeAction) {
    setRemaining((n) => Math.max(0, n - 1));
    api.swipe(rec.slug, action).catch(() => undefined);
    if (action === "like") {
      setFavorites((prev) => (prev.some((p) => p.id === rec.id) ? prev : [rec, ...prev]));
    }
  }

  function removeFavorite(slug: string) {
    setFavorites((prev) => prev.filter((p) => p.slug !== slug));
    api.unfavorite(slug).catch(() => undefined);
  }

  function startEdit() {
    setNameInput(user?.first_name || "");
    setPhoneInput(user?.telefone || "");
    setMeError("");
    setEditing(true);
  }

  async function saveProfile() {
    setSavingMe(true);
    setMeError("");
    try {
      await api.updateMe({ first_name: nameInput.trim(), telefone: phoneInput.trim() });
      await refresh();
      setEditing(false);
    } catch (err) {
      setMeError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setSavingMe(false);
    }
  }

  if (loading) {
    return <div className="min-h-screen px-6 pt-28"><div className="surface mx-auto h-64 max-w-xl animate-pulse rounded-3xl" /></div>;
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 py-28">
        <div className="glass w-full max-w-md rounded-[2rem] p-10 text-center">
          <UserIcon className="mx-auto h-10 w-10 text-gold-400" />
          <h1 className="mt-4 text-2xl font-bold">Entre na sua conta</h1>
          <p className="mt-2 text-muted-foreground">Acesse seu perfil, buscas e contratações.</p>
          <div className="mt-6 flex flex-col gap-3">
            <Link to="/entrar" className="btn-gold py-3">Entrar</Link>
            <Link to="/cadastrar" className="btn-ghost py-3">Criar conta</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">Meu perfil</h1>

        <div className="surface mt-8 rounded-3xl p-6 sm:p-8">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-gold-500/30 bg-gold-500/10 text-2xl font-bold text-gold-300">
              {(user.first_name || user.email)[0]?.toUpperCase()}
            </div>
            <div>
              <p className="flex items-center gap-2 text-xl font-bold">
                {user.first_name || "Sua conta"}
                {user.is_provider && <BadgeCheck className="h-5 w-5 text-gold-400" />}
              </p>
              <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Mail className="h-4 w-4" /> {user.email}
              </p>
            </div>
          </div>

          {editing ? (
            <div className="mt-5 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-foreground/80">Nome de exibição</span>
                <input
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  placeholder="Seu nome"
                  className="rounded-2xl border border-white/12 bg-white/5 px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-foreground/80">Telefone</span>
                <input
                  value={phoneInput}
                  onChange={(e) => setPhoneInput(e.target.value)}
                  placeholder="(11) 99999-9999"
                  className="rounded-2xl border border-white/12 bg-white/5 px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
                />
              </label>
              {meError && <p className="text-sm text-rose-400 sm:col-span-2">{meError}</p>}
              <div className="flex gap-2 sm:col-span-2">
                <button onClick={saveProfile} disabled={savingMe} className="btn-gold px-5 py-2.5 text-sm disabled:opacity-60">
                  {savingMe ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
                </button>
                <button onClick={() => setEditing(false)} className="btn-ghost px-5 py-2.5 text-sm">Cancelar</button>
              </div>
            </div>
          ) : (
            <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-foreground/75">
              {user.cpf && <span>CPF: {user.cpf}</span>}
              {user.telefone && (
                <span className="inline-flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-gold-400" /> {user.telefone}
                </span>
              )}
              <button onClick={startEdit} className="inline-flex items-center gap-1.5 text-gold-300 transition-colors hover:text-gold-200">
                <Pencil className="h-3.5 w-3.5" /> Editar perfil
              </button>
            </div>
          )}

          <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-foreground/75">
            {user.is_provider
              ? "Você tem um perfil de profissional cadastrado. Ele precisa ser aprovado por nossa equipe para aparecer na busca."
              : "Conta de cliente. Você pode contratar profissionais e, quando quiser, criar seu próprio perfil de profissional."}
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            {user.is_provider && user.provider_slug ? (
              <Link to={`/prestador/${user.provider_slug}`} className="btn-gold flex-1 py-3">
                <BadgeCheck className="h-4 w-4" /> Ver meu perfil público
              </Link>
            ) : (
              <Link to="/buscar" className="btn-gold flex-1 py-3">Buscar profissionais</Link>
            )}
            {!user.is_provider && (
              <Link to="/sou-prestador" className="btn-ghost flex-1 py-3">
                <Wrench className="h-4 w-4" /> Tornar-se profissional
              </Link>
            )}
            <button onClick={() => { logout(); navigate("/"); }} className="btn-ghost py-3 sm:px-5">
              <LogOut className="h-4 w-4" /> Sair
            </button>
          </div>
        </div>

        {/* Área administrativa: painel de logs (Django). Só aparece para staff. */}
        {user.is_staff && (
          <a
            href="/dashboard/"
            target="_blank"
            rel="noopener noreferrer"
            className="surface mt-6 flex items-center gap-4 rounded-3xl p-5 transition-colors hover:border-gold-500/40 sm:p-6"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-gold-500/30 bg-gold-500/10 text-gold-300">
              <Activity className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-2 font-semibold">
                Painel de logs
                <span className="rounded-full bg-gold-500/20 px-2 py-0.5 text-[11px] font-semibold text-gold-200">admin</span>
              </p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Requisições, erros, buscas e autenticação em tempo real — com gráficos e percentis.
              </p>
            </div>
            <span className="hidden text-sm text-gold-300 sm:inline">Abrir →</span>
          </a>
        )}

        {/* Tabs: match de prestadores + favoritos */}
        <div className="mt-10 flex flex-wrap items-center gap-2">
          <TabButton active={tab === "para-voce"} onClick={() => setTab("para-voce")}>
            <Handshake className="h-4 w-4" /> Para você
          </TabButton>
          <TabButton active={tab === "favoritos"} onClick={() => setTab("favoritos")}>
            <Heart className="h-4 w-4" /> Prestadores favoritos
            {favorites.length > 0 && (
              <span className="ml-1 rounded-full bg-gold-500/25 px-2 py-0.5 text-[11px] font-semibold text-gold-200">
                {favorites.length}
              </span>
            )}
          </TabButton>
        </div>

        {tab === "para-voce" ? (
          <section className="mt-8">
            <div className="max-w-2xl">
              <h2 className="font-display text-2xl font-semibold sm:text-3xl">
                Recomendados <span className="text-gold">pra você</span>
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Selecionados a partir do que você pesquisou: a categoria buscada, categorias
                parecidas e, de preferência, perto de você. Curta para salvar nos favoritos,
                passe para ver o próximo.
              </p>
              {!deckLoading && hasSearched && (
                <p className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-white/12 bg-white/5 px-3 py-1.5 text-xs text-foreground/70">
                  <CalendarClock className="h-3.5 w-3.5 text-gold-400" />
                  {remaining > 0
                    ? <><span className="font-semibold text-foreground">{remaining}</span> de {dailyLimit} recomendações restantes hoje</>
                    : <>Limite diário de {dailyLimit} recomendações atingido</>}
                </p>
              )}
            </div>

            <div className="mt-8 flex justify-center">
              {deckLoading ? (
                <div className="surface h-[420px] w-[340px] animate-pulse rounded-3xl opacity-60" />
              ) : !hasSearched ? (
                <div className="surface flex h-[420px] w-full max-w-[360px] flex-col items-center justify-center gap-3 rounded-3xl p-8 text-center">
                  <Search className="h-9 w-9 text-gold-400" />
                  <p className="font-display text-xl font-semibold">Use a plataforma e receba recomendações</p>
                  <p className="max-w-xs text-sm text-muted-foreground">
                    Suas indicações nascem do que você procura. Faça uma busca por um serviço
                    e a HIVEE passa a recomendar profissionais feitos pra você.
                  </p>
                  <Link to="/buscar" className="btn-gold mt-2 px-5 py-2.5 text-sm">
                    <Search className="h-4 w-4" /> Buscar profissionais
                  </Link>
                </div>
              ) : remaining <= 0 ? (
                <div className="surface flex h-[420px] w-full max-w-[360px] flex-col items-center justify-center gap-3 rounded-3xl p-8 text-center">
                  <CalendarClock className="h-9 w-9 text-gold-400" />
                  <p className="font-display text-xl font-semibold">Por hoje é só! 🌙</p>
                  <p className="max-w-xs text-sm text-muted-foreground">
                    Você já viu suas {dailyLimit} recomendações de hoje. Volte amanhã para
                    novas indicações feitas pra você.
                  </p>
                  <button onClick={() => setTab("favoritos")} className="btn-ghost mt-2 px-5 py-2.5 text-sm">
                    <Heart className="h-4 w-4" /> Ver meus favoritos
                  </button>
                </div>
              ) : (
                <SwipeDeck recs={recs} onSwipe={handleSwipe} />
              )}
            </div>
          </section>
        ) : (
          <section className="mt-8">
            <div className="max-w-2xl">
              <h2 className="font-display text-2xl font-semibold sm:text-3xl">
                Seus <span className="text-gold">favoritos</span>
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Profissionais que você curtiu no swipe. Eles ficam guardados aqui pra quando precisar.
              </p>
            </div>

            <div className="mt-8">
              {favLoading ? (
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="surface h-80 animate-pulse rounded-3xl opacity-60" />
                  ))}
                </div>
              ) : favorites.length === 0 ? (
                <div className="surface flex flex-col items-center gap-3 rounded-3xl p-16 text-center">
                  <Heart className="h-9 w-9 text-gold-400" />
                  <p className="font-display text-2xl font-semibold">Nenhum favorito ainda</p>
                  <p className="max-w-md text-sm text-muted-foreground">
                    Vá na aba <b>Para você</b> e curta os profissionais que mais combinam com você.
                  </p>
                  <button onClick={() => setTab("para-voce")} className="btn-gold mt-2 px-5 py-2.5 text-sm">
                    <Handshake className="h-4 w-4" /> Ver recomendações
                  </button>
                </div>
              ) : (
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {favorites.map((p) => (
                    <div key={p.id} className="relative">
                      <ProviderCard provider={p} />
                      <button
                        type="button"
                        onClick={() => removeFavorite(p.slug)}
                        aria-label="Remover dos favoritos"
                        className="absolute left-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full border border-white/15 bg-black/55 text-rose-300 backdrop-blur transition-colors hover:border-rose-400/60 hover:bg-rose-500/20"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? "border-gold-500/50 bg-gold-500/15 text-gold-200"
          : "border-white/12 bg-white/5 text-foreground/70 hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}
