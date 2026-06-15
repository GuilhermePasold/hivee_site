import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "@/context/NotificationsContext";
import { metaFor } from "@/lib/notifications";
import type { AppNotification } from "@/types";

const AUTO_DISMISS_MS = 6000;

/** Pilha de toasts no canto inferior direito para notificações que chegam ao vivo. */
export default function NotificationToaster() {
  const { toasts, dismissToast, markRead } = useNotifications();

  return (
    <div className="pointer-events-none fixed bottom-5 right-4 z-[60] flex w-[22rem] max-w-[calc(100vw-2rem)] flex-col gap-2 sm:right-6">
      <AnimatePresence initial={false}>
        {toasts.map((n) => (
          <Toast key={n.id} n={n} onDismiss={() => dismissToast(n.id)} onRead={markRead} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function Toast({
  n,
  onDismiss,
  onRead,
}: {
  n: AppNotification;
  onDismiss: () => void;
  onRead: (id: number) => void;
}) {
  const navigate = useNavigate();
  const { Icon, color, tint } = metaFor(n.tipo);

  useEffect(() => {
    const t = window.setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => window.clearTimeout(t);
  }, [onDismiss]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 60, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 60, scale: 0.95 }}
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      className="glass-solid pointer-events-auto relative overflow-hidden rounded-2xl border border-white/10 shadow-2xl"
    >
      <button
        onClick={() => {
          onRead(n.id);
          onDismiss();
          if (n.link) navigate(n.link);
        }}
        className="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-white/5"
      >
        <span className={`mt-0.5 grid h-9 w-9 flex-none place-items-center rounded-full ${tint}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate pr-5 text-sm font-medium text-foreground">{n.title}</span>
          {n.body && (
            <span className="mt-0.5 line-clamp-2 block text-xs leading-5 text-muted-foreground">
              {n.body}
            </span>
          )}
        </span>
      </button>
      <button
        onClick={onDismiss}
        aria-label="Dispensar"
        className="absolute right-2 top-2 grid h-6 w-6 place-items-center rounded-full text-foreground/50 transition-colors hover:bg-white/10 hover:text-foreground"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </motion.div>
  );
}
