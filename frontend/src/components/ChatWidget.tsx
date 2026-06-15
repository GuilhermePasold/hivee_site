import { ExternalLink, MapPin, Mic, Paperclip, Send, Square, Star, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

interface ProviderMini {
  id?: number;
  nome: string;
  slug: string;
  categoria: string;
  cidade?: string;
  estado?: string;
  nota?: number;
  avaliacoes?: number;
  descricao?: string;
  avatar_url?: string;
  preco_hora?: number;
  tempo_resposta?: string;
  habilidades?: string[];
  link: string;
}

type Message =
  | {
  role: "user" | "bot";
      type?: "text";
  content: string;
    }
  | {
      role: "bot";
      type: "provider_cards";
      content?: string;
      providers: ProviderMini[];
    };

interface Props {
  telefone: string;
  initialDraft?: string;
  onClose?: () => void;
}

export function ChatWidget({ telefone, initialDraft = "", onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionError, setConnectionError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const ws = useRef<WebSocket | null>(null);
  const typingTimeout = useRef<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const recordingTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (initialDraft) setInput(initialDraft);
  }, [initialDraft]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.VITE_WS_HOST || window.location.host;
    let reconnectTimer: number | null = null;
    let closedByCleanup = false;

    function connect() {
      ws.current = new WebSocket(`${protocol}//${host}/ws/chat/${telefone}/`);

      ws.current.onopen = () => {
        setConnected(true);
        setConnectionError("");
      };
      ws.current.onerror = () => {
        setConnectionError("Não consegui conectar ao chat.");
      };
      ws.current.onclose = () => {
        setConnected(false);
        setIsTyping(false);
        if (!closedByCleanup) {
          reconnectTimer = window.setTimeout(connect, 2000);
        }
      };
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "provider_cards") {
          setMessages((prev) => [
            ...prev,
            { role: "bot", type: "provider_cards", providers: data.providers || [] },
          ]);
          return;
        }
        if (data.typing) {
          setIsTyping(true);
          if (typingTimeout.current) window.clearTimeout(typingTimeout.current);
          typingTimeout.current = window.setTimeout(() => {
            setIsTyping(false);
            setConnectionError("A resposta demorou demais. Tente enviar de novo.");
          }, 45000);
          return;
        }
        if (typingTimeout.current) window.clearTimeout(typingTimeout.current);
        setConnectionError("");
        setIsTyping(false);
        if (data.content) {
          setMessages((prev) => [...prev, { role: "bot", content: data.content }]);
        }
      };
    }

    connect();

    return () => {
      closedByCleanup = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      if (typingTimeout.current) window.clearTimeout(typingTimeout.current);
      if (recordingTimerRef.current) window.clearInterval(recordingTimerRef.current);
      audioStreamRef.current?.getTracks().forEach((track) => track.stop());
      ws.current?.close();
    };
  }, [telefone]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const send = useCallback(() => {
    const content = input.trim();
    if (!content || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    ws.current.send(JSON.stringify({ content }));
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
  }, [input]);

  const sendFile = useCallback((file: File) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      setConnectionError("Conecte ao chat antes de enviar arquivos.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setConnectionError("Envie um arquivo de até 8MB.");
      return;
    }

    setUploading(true);
    const reader = new FileReader();
    reader.onload = () => {
      const content = input.trim();
      ws.current?.send(
        JSON.stringify({
          content,
          media: {
            name: file.name,
            mime_type: file.type,
            data: reader.result,
          },
        }),
      );
      const label = file.type.startsWith("audio/") ? "Áudio enviado" : "Imagem enviada";
      setMessages((prev) => [...prev, { role: "user", content: `${label}${content ? `\n${content}` : ""}` }]);
      setInput("");
      setUploading(false);
    };
    reader.onerror = () => {
      setUploading(false);
      setConnectionError("Não consegui ler esse arquivo.");
    };
    reader.readAsDataURL(file);
  }, [input]);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  }, []);

  const startRecording = useCallback(async () => {
    if (!connected || uploading || isRecording) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      setConnectionError("Seu navegador não liberou gravação de áudio aqui.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType });
      audioStreamRef.current = stream;
      audioChunksRef.current = [];
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        const file = new File([blob], `audio-hivee-${Date.now()}.webm`, { type: mimeType });
        audioChunksRef.current = [];
        stream.getTracks().forEach((track) => track.stop());
        audioStreamRef.current = null;
        mediaRecorderRef.current = null;
        setIsRecording(false);
        setRecordingSeconds(0);
        if (recordingTimerRef.current) {
          window.clearInterval(recordingTimerRef.current);
          recordingTimerRef.current = null;
        }
        if (blob.size > 0) sendFile(file);
      };

      recorder.start();
      setConnectionError("");
      setIsRecording(true);
      setRecordingSeconds(0);
      recordingTimerRef.current = window.setInterval(() => {
        setRecordingSeconds((seconds) => seconds + 1);
      }, 1000);
    } catch {
      setConnectionError("Não consegui acessar o microfone.");
      audioStreamRef.current?.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
      setIsRecording(false);
    }
  }, [connected, isRecording, sendFile, uploading]);

  return (
    <div className="fixed bottom-5 left-4 right-4 z-50 flex h-[32rem] max-h-[calc(100vh-7rem)] flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-950 shadow-2xl sm:bottom-24 sm:left-auto sm:right-6 sm:w-96">
      <div className="flex items-center gap-3 border-b border-zinc-700 bg-amber-500/10 px-4 py-3">
        <div className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
        <span className="font-medium text-zinc-100">HIVEE Chat</span>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="ml-auto grid h-8 w-8 place-items-center rounded-lg text-zinc-300 transition hover:bg-white/10 hover:text-white"
            aria-label="Fechar chat"
            title="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((msg, i) => {
          if (msg.type === "provider_cards") {
            return (
              <div key={`cards-${i}`} className="flex justify-start">
                <div className="w-full max-w-[92%] space-y-2">
                  {msg.providers.map((provider) => (
                    <ProviderMiniCard key={provider.slug || provider.nome} provider={provider} />
                  ))}
                </div>
              </div>
            );
          }

          return (
            <div key={`${msg.role}-${i}`} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] whitespace-pre-wrap px-4 py-2 text-sm ${
                  msg.role === "user"
                    ? "rounded-2xl rounded-br-md bg-amber-500 text-black"
                    : "rounded-2xl rounded-bl-md bg-zinc-800 text-zinc-100"
                }`}
              >
                {renderMessageContent(msg.content)}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-2 text-sm italic text-zinc-400">
              digitando...
            </div>
          </div>
        )}
        {connectionError && (
          <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {connectionError}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 border-t border-zinc-700 p-3">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,audio/*"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.currentTarget.value = "";
            if (file) sendFile(file);
          }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || isRecording}
          className="grid h-10 w-10 place-items-center rounded-xl bg-zinc-800 text-zinc-100 transition-colors hover:bg-zinc-700 disabled:opacity-60"
          aria-label="Anexar imagem ou áudio"
          title="Anexar imagem ou áudio"
        >
          <Paperclip className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!connected || uploading}
          className={`grid h-10 w-10 place-items-center rounded-xl transition-colors disabled:opacity-60 ${
            isRecording
              ? "bg-red-500 text-white hover:bg-red-400"
              : "bg-zinc-800 text-zinc-100 hover:bg-zinc-700"
          }`}
          aria-label={isRecording ? "Parar gravação" : "Gravar áudio"}
          title={isRecording ? `Parar gravação (${recordingSeconds}s)` : "Gravar áudio"}
        >
          {isRecording ? <Square className="h-4 w-4 fill-current" /> : <Mic className="h-4 w-4" />}
        </button>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && send()}
          placeholder="Digite sua mensagem..."
          className="min-w-0 flex-1 rounded-xl bg-zinc-800 px-4 py-2 text-sm text-zinc-100 outline-none focus:ring-1 focus:ring-amber-500"
        />
        <button
          type="button"
          onClick={send}
          disabled={!connected}
          className="grid h-10 w-10 place-items-center rounded-xl bg-amber-500 text-black transition-colors hover:bg-amber-400"
          aria-label="Enviar mensagem"
          title="Enviar"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

function renderMessageContent(content: string) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = content.split(urlRegex);
  return parts.map((part, index) => {
    if (!part.startsWith("http://") && !part.startsWith("https://")) return part;
    const cleanUrl = part.replace(/[).,!?]+$/, "");
    const suffix = part.slice(cleanUrl.length);
    const href = normalizeHiveeHref(cleanUrl);
    return (
      <span key={`${cleanUrl}-${index}`}>
        <a
          href={href}
          className="font-semibold underline decoration-current/40 underline-offset-2 hover:decoration-current"
          target={href.startsWith("http") ? "_blank" : undefined}
          rel={href.startsWith("http") ? "noreferrer" : undefined}
        >
          {cleanUrl}
        </a>
        {suffix}
      </span>
    );
  });
}

function normalizeHiveeHref(rawHref: string) {
  try {
    const url = new URL(rawHref, window.location.origin);
    if (url.hostname === "hivee.app" || url.hostname === "www.hivee.app") {
      return `${url.pathname}${url.search}${url.hash}`;
    }
  } catch {
    return rawHref;
  }
  return rawHref;
}

function ProviderMiniCard({ provider }: { provider: ProviderMini }) {
  const price =
    typeof provider.preco_hora === "number"
      ? new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(
          provider.preco_hora,
        )
      : null;

  return (
    <div className="rounded-2xl rounded-bl-md border border-zinc-700 bg-zinc-900 p-3 text-sm text-zinc-100">
      <div className="flex gap-3">
        {provider.avatar_url ? (
          <img
            src={provider.avatar_url}
            alt={provider.nome}
            className="h-12 w-12 flex-none rounded-xl object-cover"
          />
        ) : (
          <div className="grid h-12 w-12 flex-none place-items-center rounded-xl bg-amber-500/15 text-base font-semibold text-amber-300">
            {provider.nome.slice(0, 1)}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="truncate font-semibold">{provider.nome}</div>
          <div className="truncate text-xs text-zinc-400">{provider.categoria}</div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-300">
            {typeof provider.nota === "number" && (
              <span className="inline-flex items-center gap-1">
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                {provider.nota.toFixed(1)} ({provider.avaliacoes || 0})
              </span>
            )}
            {provider.cidade && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3 w-3 text-amber-400" />
                {provider.cidade}
                {provider.estado ? `, ${provider.estado}` : ""}
              </span>
            )}
          </div>
        </div>
      </div>

      {provider.descricao && <p className="mt-3 line-clamp-2 text-xs leading-5 text-zinc-300">{provider.descricao}</p>}

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-zinc-800 pt-3">
        <div className="min-w-0 text-xs text-zinc-400">
          {price && <span className="font-semibold text-zinc-100">{price}/h</span>}
          {provider.tempo_resposta && <span className="block truncate">{provider.tempo_resposta}</span>}
        </div>
        <a
          href={normalizeHiveeHref(provider.link || `/prestador/${provider.slug}`)}
          className="inline-flex h-9 flex-none items-center gap-1.5 rounded-xl bg-amber-500 px-3 text-xs font-semibold text-black transition-colors hover:bg-amber-400"
        >
          Ver perfil
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </div>
  );
}
