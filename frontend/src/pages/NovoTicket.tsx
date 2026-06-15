import { ArrowLeft, Loader2, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { SupportCategory } from "@/types";

const PRIORITIES = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Média" },
  { value: "high", label: "Alta" },
  { value: "urgent", label: "Urgente" },
];

export default function NovoTicket() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState<SupportCategory[]>([]);
  const [categorySlug, setCategorySlug] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;
    api.faqCategories().then(setCategories).catch(() => undefined);
  }, [user]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!subject.trim() || !description.trim()) {
      setError("Preencha o assunto e a descrição.");
      return;
    }
    setSubmitting(true);
    try {
      const ticket = await api.createSupportTicket({
        subject: subject.trim(),
        description: description.trim(),
        category_slug: categorySlug || undefined,
        priority,
      });
      navigate(`/suporte/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível abrir o ticket.");
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className="min-h-screen px-6 pt-28"><div className="surface mx-auto h-64 max-w-xl animate-pulse rounded-3xl" /></div>;
  }
  if (!user) return <Navigate to="/entrar" replace />;

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-2xl">
        <Link to="/suporte/tickets" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-gold-300">
          <ArrowLeft className="h-4 w-4" /> Meus tickets
        </Link>

        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-tight">
          Abrir <span className="text-gold">ticket</span>
        </h1>
        <p className="mt-2 text-muted-foreground">
          Descreva sua solicitação com detalhes. Nossa equipe responde por aqui e você recebe um aviso.
        </p>

        <form onSubmit={submit} className="surface mt-8 flex flex-col gap-5 rounded-3xl p-6 sm:p-8">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground/80">Categoria (opcional)</span>
            <select
              value={categorySlug}
              onChange={(e) => setCategorySlug(e.target.value)}
              className="rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground focus:border-gold-500/50 focus:outline-none"
            >
              <option value="">Selecione um assunto</option>
              {categories.map((c) => (
                <option key={c.slug} value={c.slug} className="bg-zinc-900">
                  {c.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground/80">Assunto</span>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={200}
              placeholder="Resumo da sua solicitação"
              className="rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground/80">Descrição</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              placeholder="Conte o que aconteceu, com datas, valores e o que você espera."
              className="resize-y rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground/80">Prioridade</span>
            <div className="flex flex-wrap gap-2">
              {PRIORITIES.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPriority(p.value)}
                  className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    priority === p.value
                      ? "border-gold-500/50 bg-gold-500/15 text-gold-200"
                      : "border-white/12 bg-white/5 text-foreground/70 hover:text-foreground"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </label>

          {error && <p className="text-sm text-rose-400">{error}</p>}

          <button disabled={submitting} className="btn-gold mt-1 py-3.5 text-base disabled:opacity-60">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Send className="h-4 w-4" /> Enviar ticket</>}
          </button>
        </form>
      </div>
    </div>
  );
}
