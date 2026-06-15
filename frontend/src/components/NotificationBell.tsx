import { AnimatePresence, motion } from "framer-motion";
import { Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNotifications } from "@/context/NotificationsContext";
import NotificationPanel from "@/components/NotificationPanel";

export default function NotificationBell() {
  const { unread } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Fecha ao clicar fora ou apertar Esc.
  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const badge = unread > 99 ? "99+" : String(unread);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={unread > 0 ? `Notificações (${unread} não lidas)` : "Notificações"}
        aria-expanded={open}
        className="btn-ghost relative grid h-9 w-9 place-items-center rounded-full"
      >
        <Bell className="h-4 w-4" />
        <AnimatePresence>
          {unread > 0 && (
            <motion.span
              key="badge"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 25 }}
              className="absolute -right-0.5 -top-0.5 grid min-w-4 place-items-center rounded-full bg-gold-500 px-1 text-[10px] font-bold leading-4 text-black"
            >
              {badge}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      <AnimatePresence>{open && <NotificationPanel onClose={() => setOpen(false)} />}</AnimatePresence>
    </div>
  );
}
