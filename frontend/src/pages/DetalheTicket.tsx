import { ArrowLeft, CheckCircle2, Loader2, RotateCcw, Send, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import TicketStatusBadge, { TicketPriorityBadge } from "@/components/TicketStatusBadge";
import type { SupportTicket, SupportTicketStatus } from "@/types";

const TRANSITION_META: Record<
  SupportTicketStatus,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  open: { label: "Reabrir", icon: RotateCcw, className: "btn-ghost" },
  waiting_user: { label: "Aguardar usuário", icon: RotateCcw, className: "btn-ghost" },
  waiting_staff: { label: "Reabrir para equipe", icon: RotateCcw, className: "btn-ghost" },
  resolved: { label: "Marcar resolvido", icon: CheckCircle2, className: "btn-gold" },
  closed: { label: "Fechar ticket", icon: XCircle, className: "btn-ghost" },
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DetalheTicket() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [busy, setBusy] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [transitioning, setTransitioning] = useState<string | null>(null);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user || !id) return;
    let active = true;
    setBusy(true);
    api
      .supportTicket(Number(id))
      .then((t) => active && setTicket(t))
      .catch(() => active && setNotFound(true))
      .finally(() => active && setBusy(false));
    return () => {
      active = false;
    };
  }, [user, id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [ticket?.messages.length]);

  async function sendReply(e: React.FormEvent) {
    e.preventDefault();
    const content = reply.trim();
    if (!content || !ticket) return;
    setSending(true);
    setError("");
    try {
      await api.sendTicketMessage(ticket.id, content);
      setReply("");
      const fresh = await api.supportTicket(ticket.id);
      setTicket(fresh);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível enviar.");
    } finally {
      setSending(false);
    }
  }

  async function doTransition(status: SupportTicketStatus) {
    if (!ticket) return;
    setTransitioning(status);
    setError("");
    try {
      const updated = await api.transitionTicket(ticket.id, status);
      setTicket(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível atualizar o status.");
    } finally {
      setTransitioning(null);
    }
  }

  if (loading) {
    return <div className="min-h-screen px-6 pt-28"><div className="surface mx-auto h-64 max-w-3xl animate-pulse rounded-3xl" /></div>;
  }
  if (!user) return <Navigate to="/entrar" replace />;

  if (notFound) {
    return (
      <div className="min-h-screen px-6 pb-24 pt-28">
        <div className="surface mx-auto max-w-xl rounded-3xl p-10 text-center">
          <p className="font-display text-2xl font-semibold">Ticket não encontrado</p>
          <p className="mt-2 text-sm text-muted-foreground">Ele não existe ou não é seu.</p>
          <Link to="/suporte/tickets" className="btn-gold mt-6 inline-flex px-5 py-2.5 text-sm">
            Voltar para meus tickets
          </Link>
        </div>
      </div>
    );
  }

  const isClosed = ticket?.status === "closed";

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-3xl">
        <Link to="/suporte/tickets" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-gold-300">
          <ArrowLeft className="h-4 w-4" /> Meus tickets
        </Link>

        {busy || !ticket ? (
          <div className="surface mt-4 h-96 animate-pulse rounded-3xl opacity-60" />
        ) : (
          <>
            {/* Cabeçalho */}
            <div className="surface mt-4 rounded-3xl p-6 sm:p-7">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h1 className="font-display text-2xl font-bold leading-tight sm:text-3xl">{ticket.subject}</h1>
                  <p className="mt-1 text-xs text-muted-foreground">
                    #{ticket.id}
                    {ticket.category ? ` · ${ticket.category.name}` : ""} · aberto em {formatDateTime(ticket.created_at)}
                  </p>
                </div>
                <div className="flex flex-none flex-col items-end gap-1.5">
                  <TicketStatusBadge status={ticket.status} />
                  <TicketPriorityBadge priority={ticket.priority} />
                </div>
              </div>
              <p className="mt-4 whitespace-pre-wrap border-t border-white/8 pt-4 text-sm leading-relaxed text-foreground/80">
                {ticket.description}
              </p>
            </div>

            {/* Conversa */}
            <section className="mt-6">
              <h2 className="font-display text-lg font-semibold text-foreground/80">Conversa</h2>
              <div className="mt-3 space-y-3">
                {ticket.messages.length === 0 ? (
                  <p className="surface rounded-2xl p-6 text-center text-sm text-muted-foreground">
                    Ainda não há mensagens. Nossa equipe responderá em breve.
                  </p>
                ) : (
                  ticket.messages.map((m) => (
                    <div key={m.id} className={`flex ${m.is_staff ? "justify-start" : "justify-end"}`}>
                      <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                        m.is_staff
                          ? "rounded-bl-md border border-gold-500/25 bg-gold-500/10 text-foreground"
                          : "rounded-br-md bg-white/8 text-foreground"
                      }`}>
                        <div className="mb-1 flex items-center gap-1.5 text-xs">
                          {m.is_staff && <ShieldCheck className="h-3.5 w-3.5 text-gold-400" />}
                          <span className={`font-semibold ${m.is_staff ? "text-gold-300" : "text-foreground/70"}`}>
                            {m.is_staff ? "Equipe HIVEE" : m.author_name}
                          </span>
                          <span className="text-muted-foreground">· {formatDateTime(m.created_at)}</span>
                        </div>
                        <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                      </div>
                    </div>
                  ))
                )}
                <div ref={bottomRef} />
              </div>
            </section>

            {error && <p className="mt-4 text-sm text-rose-400">{error}</p>}

            {/* Responder */}
            {isClosed ? (
              <p className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-center text-sm text-muted-foreground">
                Este ticket está fechado. Precisa de mais ajuda?{" "}
                <Link to="/suporte/novo" className="text-gold-300 hover:underline">Abra um novo ticket</Link>.
              </p>
            ) : (
              <form onSubmit={sendReply} className="surface mt-6 rounded-3xl p-4">
                <textarea
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  rows={3}
                  placeholder="Escreva sua resposta..."
                  className="w-full resize-y rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
                />
                <div className="mt-3 flex items-center justify-end">
                  <button disabled={sending || !reply.trim()} className="btn-gold px-5 py-2.5 text-sm disabled:opacity-50">
                    {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4" /> Enviar</>}
                  </button>
                </div>
              </form>
            )}

            {/* Transições */}
            {ticket.can_transition.length > 0 && (
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <span className="text-sm text-muted-foreground">Ações:</span>
                {ticket.can_transition.map((status) => {
                  const meta = TRANSITION_META[status];
                  const Icon = meta.icon;
                  return (
                    <button
                      key={status}
                      type="button"
                      onClick={() => doTransition(status)}
                      disabled={transitioning !== null}
                      className={`${meta.className} px-4 py-2 text-sm disabled:opacity-50`}
                    >
                      {transitioning === status ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <><Icon className="h-4 w-4" /> {meta.label}</>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
