import { Inbox, Plus, Ticket } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import TicketStatusBadge, { TicketPriorityBadge } from "@/components/TicketStatusBadge";
import type { SupportTicket } from "@/types";

type Tab = "abertos" | "resolvidos" | "fechados";

const OPEN_STATUSES = new Set(["open", "waiting_user", "waiting_staff"]);

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function MeusTickets() {
  const { user, loading } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [tab, setTab] = useState<Tab>("abertos");
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    if (!user) return;
    let active = true;
    setBusy(true);
    api
      .supportTickets()
      .then((r) => active && setTickets(r.results))
      .catch(() => undefined)
      .finally(() => active && setBusy(false));
    return () => {
      active = false;
    };
  }, [user]);

  const groups = useMemo(() => {
    return {
      abertos: tickets.filter((t) => OPEN_STATUSES.has(t.status)),
      resolvidos: tickets.filter((t) => t.status === "resolved"),
      fechados: tickets.filter((t) => t.status === "closed"),
    };
  }, [tickets]);

  if (loading) {
    return <div className="min-h-screen px-6 pt-28"><div className="surface mx-auto h-64 max-w-3xl animate-pulse rounded-3xl" /></div>;
  }
  if (!user) return <Navigate to="/entrar" replace />;

  const visible = groups[tab];

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Ticket className="h-8 w-8 text-gold-400" />
            <h1 className="font-display text-4xl font-extrabold tracking-tight sm:text-5xl">
              Meus <span className="text-gold">tickets</span>
            </h1>
          </div>
          <Link to="/suporte/novo" className="btn-gold px-5 py-2.5 text-sm">
            <Plus className="h-4 w-4" /> Novo ticket
          </Link>
        </div>

        {/* Tabs */}
        <div className="mt-8 flex flex-wrap gap-2">
          <TabButton active={tab === "abertos"} onClick={() => setTab("abertos")} count={groups.abertos.length}>
            Em aberto
          </TabButton>
          <TabButton active={tab === "resolvidos"} onClick={() => setTab("resolvidos")} count={groups.resolvidos.length}>
            Resolvidos
          </TabButton>
          <TabButton active={tab === "fechados"} onClick={() => setTab("fechados")} count={groups.fechados.length}>
            Fechados
          </TabButton>
        </div>

        <div className="mt-6 space-y-3">
          {busy ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="surface h-28 animate-pulse rounded-2xl opacity-60" />
            ))
          ) : visible.length === 0 ? (
            <div className="surface flex flex-col items-center gap-3 rounded-3xl p-14 text-center">
              <Inbox className="h-9 w-9 text-gold-400" />
              <p className="font-display text-2xl font-semibold">Nenhum ticket aqui</p>
              <p className="max-w-md text-sm text-muted-foreground">
                {tab === "abertos"
                  ? "Você não tem solicitações em aberto. Precisa de ajuda? Abra um ticket."
                  : "Nada nesta aba por enquanto."}
              </p>
              {tab === "abertos" && (
                <Link to="/suporte/novo" className="btn-gold mt-2 px-5 py-2.5 text-sm">
                  <Plus className="h-4 w-4" /> Abrir ticket
                </Link>
              )}
            </div>
          ) : (
            visible.map((t) => {
              const last = t.messages[t.messages.length - 1];
              return (
                <Link
                  key={t.id}
                  to={`/suporte/tickets/${t.id}`}
                  className="surface card-hover block rounded-2xl p-5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-semibold">{t.subject}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        #{t.id}
                        {t.category ? ` · ${t.category.name}` : ""} · atualizado em {formatDate(t.updated_at)}
                      </p>
                    </div>
                    <div className="flex flex-none flex-col items-end gap-1.5">
                      <TicketStatusBadge status={t.status} />
                      <TicketPriorityBadge priority={t.priority} />
                    </div>
                  </div>
                  {last && (
                    <p className="mt-3 line-clamp-2 text-sm text-foreground/70">
                      <span className="font-medium text-foreground/80">
                        {last.is_staff ? "Equipe HIVEE" : "Você"}:
                      </span>{" "}
                      {last.content}
                    </p>
                  )}
                </Link>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  count,
  children,
}: {
  active: boolean;
  onClick: () => void;
  count: number;
  children: React.ReactNode;
}) {
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
      <span className={`rounded-full px-1.5 text-[11px] font-semibold ${active ? "bg-gold-500/25 text-gold-100" : "bg-white/10 text-foreground/60"}`}>
        {count}
      </span>
    </button>
  );
}
