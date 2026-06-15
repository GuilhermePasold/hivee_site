import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { MessageCircle } from "lucide-react";

import { ChatWidget } from "@/components/ChatWidget";
import { GuestChatWidget } from "@/components/GuestChatWidget";
import { useAuth } from "@/context/AuthContext";

interface OpenChatOptions {
  draft?: string;
}

interface ChatCtx {
  openChat: (options?: OpenChatOptions) => void;
  closeChat: () => void;
}

const Ctx = createContext<ChatCtx | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");

  function openChat(options?: OpenChatOptions) {
    setDraft(options?.draft || "");
    setOpen(true);
  }

  function closeChat() {
    setOpen(false);
  }

  const value = useMemo(() => ({ openChat, closeChat }), [loading, user]);
  const telefone = user ? `site_user_${user.id}` : "";

  return (
    <Ctx.Provider value={value}>
      {children}
      {open && user && <ChatWidget telefone={telefone} initialDraft={draft} onClose={closeChat} />}
      {open && !loading && !user && <GuestChatWidget onClose={closeChat} />}
      {!open && (
        <button
          type="button"
          onClick={() => openChat()}
          className="fixed bottom-5 right-5 z-50 grid h-14 w-14 place-items-center rounded-full bg-gold-500 text-black shadow-2xl shadow-gold-500/20 transition hover:bg-gold-400"
          aria-label="Abrir chat HIVEE"
          title="Abrir chat"
        >
          <MessageCircle className="h-6 w-6" />
        </button>
      )}
    </Ctx.Provider>
  );
}

export function useChat() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
