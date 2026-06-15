import type { SupportTicketPriority, SupportTicketStatus } from "@/types";

const STATUS_META: Record<SupportTicketStatus, { label: string; className: string }> = {
  open: {
    label: "Aberto",
    className: "border-sky-400/40 bg-sky-500/15 text-sky-200",
  },
  waiting_user: {
    label: "Aguardando você",
    className: "border-amber-400/40 bg-amber-500/15 text-amber-200",
  },
  waiting_staff: {
    label: "Aguardando equipe",
    className: "border-orange-400/40 bg-orange-500/15 text-orange-200",
  },
  resolved: {
    label: "Resolvido",
    className: "border-emerald-400/40 bg-emerald-500/15 text-emerald-200",
  },
  closed: {
    label: "Fechado",
    className: "border-white/15 bg-white/8 text-foreground/60",
  },
};

const PRIORITY_META: Record<SupportTicketPriority, { label: string; className: string }> = {
  low: { label: "Baixa", className: "border-white/15 bg-white/8 text-foreground/60" },
  medium: { label: "Média", className: "border-sky-400/40 bg-sky-500/10 text-sky-200" },
  high: { label: "Alta", className: "border-orange-400/40 bg-orange-500/15 text-orange-200" },
  urgent: { label: "Urgente", className: "border-rose-400/50 bg-rose-500/15 text-rose-200" },
};

const BASE = "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold";

export default function TicketStatusBadge({ status }: { status: SupportTicketStatus }) {
  const meta = STATUS_META[status] ?? STATUS_META.open;
  return <span className={`${BASE} ${meta.className}`}>{meta.label}</span>;
}

export function TicketPriorityBadge({ priority }: { priority: SupportTicketPriority }) {
  const meta = PRIORITY_META[priority] ?? PRIORITY_META.medium;
  return <span className={`${BASE} ${meta.className}`}>{meta.label}</span>;
}
