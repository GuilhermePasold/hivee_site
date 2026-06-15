import { AnimatePresence, motion } from "framer-motion";
import { CheckCheck, Inbox } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "@/context/NotificationsContext";
import { metaFor, timeAgo } from "@/lib/notifications";
import type { AppNotification } from "@/types";

export default function NotificationPanel({ onClose }: { onClose: () => void }) {
  const { items, unread, markRead, markAllRead } = useNotifications();
  const navigate = useNavigate();

  function open(n: AppNotification) {
    if (!n.is_read) markRead(n.id);
    onClose();
    if (n.link) navigate(n.link);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.98 }}
      transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
      className="glass-solid absolute right-0 top-12 z-50 w-[22rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-3xl border border-white/10 shadow-2xl"
    >
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <span className="font-display text-base font-semibold text-foreground">Notificações</span>
        {unread > 0 && (
          <button
            onClick={markAllRead}
            className="inline-flex items-center gap-1 text-xs text-gold-300 transition-colors hover:text-gold-200"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Marcar todas
          </button>
        )}
      </header>

      <div className="max-h-[26rem] overflow-y-auto">
        {items.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
            <Inbox className="h-8 w-8 text-foreground/30" />
            <p className="text-sm text-muted-foreground">Nenhuma notificação por aqui ainda.</p>
          </div>
        ) : (
          <ul className="divide-y divide-white/5">
            <AnimatePresence initial={false}>
              {items.map((n) => {
                const { Icon, color, tint } = metaFor(n.tipo);
                return (
                  <motion.li
                    key={n.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <button
                      onClick={() => open(n)}
                      className={`flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-white/5 ${
                        n.is_read ? "" : "bg-gold-500/[0.06]"
                      }`}
                    >
                      <span className={`mt-0.5 grid h-9 w-9 flex-none place-items-center rounded-full ${tint}`}>
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
                          <span className="mt-0.5 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                            {n.body}
                          </span>
                        )}
                      </span>
                      {!n.is_read && (
                        <span className="mt-2 h-2 w-2 flex-none rounded-full bg-gold-400" aria-hidden />
                      )}
                    </button>
                  </motion.li>
                );
              })}
            </AnimatePresence>
          </ul>
        )}
      </div>

      <footer className="border-t border-white/10 px-4 py-2.5 text-center">
        <button
          onClick={() => {
            onClose();
            navigate("/notificacoes");
          }}
          className="text-sm text-foreground/80 transition-colors hover:text-gold-300"
        >
          Ver todas
        </button>
      </footer>
    </motion.div>
  );
}
