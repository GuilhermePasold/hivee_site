import { AnimatePresence, motion } from "framer-motion";
import { Bell, CheckCheck, Inbox, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationsContext";
import { api } from "@/lib/api";
import { metaFor, timeAgo } from "@/lib/notifications";
import type { AppNotification } from "@/types";

type Filter = "todas" | "nao-lidas";

const PAGE_SIZE = 20;

/** Rótulo do grupo (Hoje, Ontem, Esta semana, Mais antigas) para uma data ISO. */
function groupLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const day = 86_400_000;
  const t = d.getTime();
  if (t >= startOfToday) return "Hoje";
  if (t >= startOfToday - day) return "Ontem";
  if (t >= startOfToday - 7 * day) return "Esta semana";
  return "Mais antigas";
}

export default function Notificacoes() {
  const { user, loading: authLoading } = useAuth();
  const { markRead, markAllRead } = useNotifications();
  const navigate = useNavigate();

  const [filter, setFilter] = useState<Filter>("todas");
  const [items, setItems] = useState<AppNotification[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const load = useCallback(
    (nextPage: number, replace: boolean) => {
      if (replace) setLoading(true);
      else setLoadingMore(true);
      api
        .notifications({
          page: nextPage,
          page_size: PAGE_SIZE,
          ...(filter === "nao-lidas" ? { unread_only: 1 } : {}),
        })
        .then((res) => {
          setItems((prev) => (replace ? res.results : [...prev, ...res.results]));
          setHasNext(Boolean(res.next));
          setPage(nextPage);
        })
        .catch(() => undefined)
        .finally(() => {
          setLoading(false);
          setLoadingMore(false);
        });
    },
    [filter],
  );

  useEffect(() => {
    if (user) load(1, true);
  }, [user, filter, load]);

  function open(n: AppNotification) {
    if (!n.is_read) {
      markRead(n.id);
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    }
    if (n.link) navigate(n.link);
  }

  function handleMarkAll() {
    markAllRead();
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    if (filter === "nao-lidas") setItems([]);
  }

  if (authLoading) {
    return (
      <div className="min-h-screen px-6 pt-28">
        <div className="surface mx-auto h-64 max-w-2xl animate-pulse rounded-3xl" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 py-28">
        <div className="glass w-full max-w-md rounded-[2rem] p-10 text-center">
          <Bell className="mx-auto h-10 w-10 text-gold-400" />
          <h1 className="mt-4 text-2xl font-bold">Entre para ver suas notificações</h1>
          <p className="mt-2 text-muted-foreground">
            Acompanhe aprovações, mensagens e atualizações dos seus serviços.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Link to="/entrar" className="btn-gold py-3">Entrar</Link>
            <Link to="/cadastrar" className="btn-ghost py-3">Criar conta</Link>
          </div>
        </div>
      </div>
    );
  }

  // Agrupa preservando a ordem (já vem mais recente primeiro do backend).
  const groups: { label: string; items: AppNotification[] }[] = [];
  for (const n of items) {
    const label = groupLabel(n.created_at);
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.items.push(n);
    else groups.push({ label, items: [n] });
  }

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-2xl">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-3xl font-bold text-foreground sm:text-4xl">Notificações</h1>
            <p className="mt-1 text-sm text-muted-foreground">Tudo o que aconteceu na sua conta.</p>
          </div>
          <button
            onClick={handleMarkAll}
            className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-foreground/80 transition-colors hover:border-gold-500/40 hover:text-foreground"
          >
            <CheckCheck className="h-4 w-4 text-gold-400" />
            Marcar todas
          </button>
        </header>

        <div className="mb-5 inline-flex rounded-full border border-white/10 bg-white/5 p-1">
          {(["todas", "nao-lidas"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
                filter === f ? "bg-gold-500/20 text-gold-200" : "text-foreground/70 hover:text-foreground"
              }`}
            >
              {f === "todas" ? "Todas" : "Não lidas"}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="surface h-20 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="glass flex flex-col items-center gap-3 rounded-3xl px-6 py-16 text-center">
            <Inbox className="h-10 w-10 text-foreground/30" />
            <p className="text-muted-foreground">
              {filter === "nao-lidas" ? "Nenhuma notificação não lida." : "Você ainda não tem notificações."}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {groups.map((group) => (
              <section key={group.label}>
                <h2 className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {group.label}
                </h2>
                <ul className="glass-solid overflow-hidden rounded-2xl border border-white/10">
                  <AnimatePresence initial={false}>
                    {group.items.map((n) => {
                      const { Icon, color, tint } = metaFor(n.tipo);
                      return (
                        <motion.li key={n.id} layout exit={{ opacity: 0 }} className="border-b border-white/5 last:border-0">
                          <button
                            onClick={() => open(n)}
                            className={`flex w-full items-start gap-3 px-4 py-4 text-left transition-colors hover:bg-white/5 ${
                              n.is_read ? "" : "bg-gold-500/[0.06]"
                            }`}
                          >
                            <span className={`mt-0.5 grid h-10 w-10 flex-none place-items-center rounded-full ${tint}`}>
                              <Icon className={`h-5 w-5 ${color}`} />
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="flex items-center justify-between gap-2">
                                <span className="truncate text-sm font-medium text-foreground">{n.title}</span>
                                <span className="flex-none text-[11px] text-muted-foreground">
                                  {timeAgo(n.created_at)}
                                </span>
                              </span>
                              {n.body && (
                                <span className="mt-0.5 block text-sm leading-5 text-muted-foreground">{n.body}</span>
                              )}
                            </span>
                            {!n.is_read && <span className="mt-2 h-2 w-2 flex-none rounded-full bg-gold-400" aria-hidden />}
                          </button>
                        </motion.li>
                      );
                    })}
                  </AnimatePresence>
                </ul>
              </section>
            ))}

            {hasNext && (
              <div className="flex justify-center pt-2">
                <button
                  onClick={() => load(page + 1, false)}
                  disabled={loadingMore}
                  className="btn-ghost inline-flex items-center gap-2 px-6 py-2.5 text-sm disabled:opacity-60"
                >
                  {loadingMore && <Loader2 className="h-4 w-4 animate-spin" />}
                  Carregar mais
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
