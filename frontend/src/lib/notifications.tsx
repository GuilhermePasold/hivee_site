import {
  AlertTriangle,
  BadgeCheck,
  Ban,
  Bell,
  CalendarCheck,
  CheckCircle2,
  FileText,
  MapPin,
  MessageSquare,
  Play,
  ShieldCheck,
  Sparkles,
  Star,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import type { NotificationTipo } from "@/types";

interface NotificationMeta {
  Icon: LucideIcon;
  /** Tailwind text color for the icon. */
  color: string;
  /** Tailwind background tint for the icon chip. */
  tint: string;
}

export const NOTIFICATION_META: Record<NotificationTipo, NotificationMeta> = {
  provider_approved: { Icon: BadgeCheck, color: "text-emerald-400", tint: "bg-emerald-400/10" },
  provider_rejected: { Icon: XCircle, color: "text-rose-400", tint: "bg-rose-400/10" },
  cpf_verified: { Icon: ShieldCheck, color: "text-emerald-400", tint: "bg-emerald-400/10" },
  cpf_mismatch: { Icon: AlertTriangle, color: "text-amber-400", tint: "bg-amber-400/10" },
  order_requested: { Icon: FileText, color: "text-blue-400", tint: "bg-blue-400/10" },
  order_confirmed: { Icon: CalendarCheck, color: "text-gold-400", tint: "bg-gold-500/10" },
  order_in_progress: { Icon: Play, color: "text-cyan-400", tint: "bg-cyan-400/10" },
  order_completed: { Icon: CheckCircle2, color: "text-emerald-400", tint: "bg-emerald-400/10" },
  order_cancelled: { Icon: Ban, color: "text-zinc-400", tint: "bg-zinc-400/10" },
  order_disputed: { Icon: AlertTriangle, color: "text-rose-400", tint: "bg-rose-400/10" },
  order_reviewed: { Icon: Star, color: "text-gold-400", tint: "bg-gold-500/10" },
  new_message: { Icon: MessageSquare, color: "text-blue-400", tint: "bg-blue-400/10" },
  new_provider_in_area: { Icon: MapPin, color: "text-gold-400", tint: "bg-gold-500/10" },
  recommendation: { Icon: Sparkles, color: "text-gold-400", tint: "bg-gold-500/10" },
};

const FALLBACK_META: NotificationMeta = {
  Icon: Bell,
  color: "text-foreground/70",
  tint: "bg-white/10",
};

export function metaFor(tipo: NotificationTipo): NotificationMeta {
  return NOTIFICATION_META[tipo] ?? FALLBACK_META;
}

/** Tempo relativo curto em pt-BR (ex.: "agora", "5 min", "3 h", "ontem"). */
export function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Math.max(0, Date.now() - then);
  const sec = Math.floor(diff / 1000);
  if (sec < 45) return "agora";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} h`;
  const days = Math.floor(hr / 24);
  if (days === 1) return "ontem";
  if (days < 7) return `${days} dias`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `${weeks} sem`;
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}
