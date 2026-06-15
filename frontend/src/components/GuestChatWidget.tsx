import { HelpCircle, LogIn, UserPlus, Wrench, X } from "lucide-react";
import { Link } from "react-router-dom";

interface Props {
  onClose: () => void;
}

export function GuestChatWidget({ onClose }: Props) {
  return (
    <div className="fixed bottom-5 left-4 right-4 z-50 flex max-h-[calc(100vh-7rem)] flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-950 shadow-2xl sm:bottom-24 sm:left-auto sm:right-6 sm:w-96">
      <div className="flex items-center gap-3 border-b border-zinc-700 bg-amber-500/10 px-4 py-3">
        <div className="h-2 w-2 rounded-full bg-amber-400" />
        <span className="font-medium text-zinc-100">Vee da HIVEE</span>
        <button
          type="button"
          onClick={onClose}
          className="ml-auto grid h-8 w-8 place-items-center rounded-lg text-zinc-300 transition hover:bg-white/10 hover:text-white"
          aria-label="Fechar chat"
          title="Fechar"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-4 p-4">
        <div className="max-w-[88%] rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-3 text-sm leading-5 text-zinc-100">
          Oi! Eu sou a Vee, agente da HIVEE. Para eu te ajudar pelo chat, salvar profissionais ou abrir um ticket,
          você precisa entrar ou criar uma conta.
        </div>

        <div className="grid gap-2">
          <Link
            to="/cadastrar"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-3 text-sm font-semibold text-black transition hover:bg-amber-400"
          >
            <UserPlus className="h-4 w-4" />
            Criar conta
          </Link>
          <Link
            to="/entrar"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm font-medium text-zinc-100 transition hover:bg-zinc-800"
          >
            <LogIn className="h-4 w-4 text-amber-300" />
            Entrar
          </Link>
          <Link
            to="/sou-prestador"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm font-medium text-zinc-100 transition hover:bg-zinc-800"
          >
            <Wrench className="h-4 w-4 text-amber-300" />
            Quero ser prestador
          </Link>
          <Link
            to="/ajuda"
            onClick={onClose}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm font-medium text-zinc-100 transition hover:bg-zinc-800"
          >
            <HelpCircle className="h-4 w-4 text-amber-300" />
            Central de ajuda
          </Link>
        </div>
      </div>
    </div>
  );
}
