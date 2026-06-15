import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { AppNotification } from "@/types";

interface NotificationsCtx {
  /** Notificações recentes (alimenta o sino/painel), mais novas primeiro. */
  items: AppNotification[];
  unread: number;
  connected: boolean;
  /** Fila de toasts a renderizar (chegadas ao vivo). */
  toasts: AppNotification[];
  dismissToast: (id: number) => void;
  markRead: (id: number) => void;
  markAllRead: () => void;
  refresh: () => void;
}

const Ctx = createContext<NotificationsCtx | null>(null);

const RECENT_LIMIT = 30;

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [connected, setConnected] = useState(false);
  const [toasts, setToasts] = useState<AppNotification[]>([]);
  const ws = useRef<WebSocket | null>(null);

  const refresh = useCallback(() => {
    if (!user) return;
    api
      .notifications({ page_size: RECENT_LIMIT })
      .then((res) => setItems(res.results))
      .catch(() => undefined);
    api
      .unreadNotificationCount()
      .then((res) => setUnread(res.count))
      .catch(() => undefined);
  }, [user]);

  // Carga inicial + WebSocket em tempo real, ligados ao ciclo de vida do login.
  useEffect(() => {
    if (!user) {
      setItems([]);
      setUnread(0);
      setToasts([]);
      setConnected(false);
      return;
    }

    refresh();

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.VITE_WS_HOST || window.location.host;
    let reconnectTimer: number | null = null;
    let closedByCleanup = false;

    function connect() {
      const socket = new WebSocket(`${protocol}//${host}/ws/notifications/`);
      ws.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        if (!closedByCleanup) reconnectTimer = window.setTimeout(connect, 3000);
      };
      socket.onmessage = (event) => {
        let data: { type?: string; data?: AppNotification; count?: number };
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }

        if (data.type === "unread_count" && typeof data.count === "number") {
          setUnread(data.count);
          return;
        }

        if (data.type === "notification" && data.data) {
          const incoming = data.data;
          setItems((prev) => {
            if (prev.some((n) => n.id === incoming.id)) return prev;
            return [incoming, ...prev].slice(0, RECENT_LIMIT);
          });
          setUnread((u) => u + 1);
          setToasts((prev) => [incoming, ...prev].slice(0, 4));
        }
      };
    }

    connect();

    return () => {
      closedByCleanup = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      ws.current?.close();
      ws.current = null;
    };
  }, [user, refresh]);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const markRead = useCallback((id: number) => {
    setItems((prev) => {
      const target = prev.find((n) => n.id === id);
      if (target && !target.is_read) setUnread((u) => Math.max(0, u - 1));
      return prev.map((n) => (n.id === id ? { ...n, is_read: true } : n));
    });
    api.markNotificationRead(id).catch(() => undefined);
  }, []);

  const markAllRead = useCallback(() => {
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnread(0);
    api.markAllNotificationsRead().catch(() => undefined);
  }, []);

  return (
    <Ctx.Provider
      value={{ items, unread, connected, toasts, dismissToast, markRead, markAllRead, refresh }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useNotifications must be used within NotificationsProvider");
  return ctx;
}
