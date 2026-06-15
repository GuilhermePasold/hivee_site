import { ChevronRight, MessageCircle, Plus, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useChat } from "@/context/ChatContext";
import { api } from "@/lib/api";
import type { FAQArticle } from "@/types";

export default function ArtigoAjuda() {
  const { slug } = useParams<{ slug: string }>();
  const { openChat } = useChat();
  const [article, setArticle] = useState<FAQArticle | null>(null);
  const [busy, setBusy] = useState(true);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  useEffect(() => {
    if (!slug) return;
    let active = true;
    setBusy(true);
    api
      .faq()
      .then((all) => active && setArticle(all.find((a) => a.slug === slug) ?? null))
      .catch(() => undefined)
      .finally(() => active && setBusy(false));
    return () => {
      active = false;
    };
  }, [slug]);

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-3xl">
        {/* Breadcrumb */}
        <nav className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
          <Link to="/ajuda" className="hover:text-gold-300">Ajuda</Link>
          {article?.category && (
            <>
              <ChevronRight className="h-4 w-4" />
              <Link to={`/ajuda?category=${article.category.slug}`} className="hover:text-gold-300">
                {article.category.name}
              </Link>
            </>
          )}
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground/70">{article ? article.question : "Artigo"}</span>
        </nav>

        {busy ? (
          <div className="surface mt-6 h-64 animate-pulse rounded-3xl opacity-60" />
        ) : !article ? (
          <div className="surface mt-6 rounded-3xl p-10 text-center">
            <p className="font-display text-2xl font-semibold">Artigo não encontrado</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Ele pode ter sido removido. Volte à Central de Ajuda.
            </p>
            <Link to="/ajuda" className="btn-gold mt-6 inline-flex px-5 py-2.5 text-sm">Voltar para a Ajuda</Link>
          </div>
        ) : (
          <>
            <article className="surface mt-6 rounded-3xl p-7 sm:p-9">
              <h1 className="font-display text-3xl font-bold leading-tight">{article.question}</h1>
              <div className="mt-5 whitespace-pre-wrap text-base leading-relaxed text-foreground/85">
                {article.answer}
              </div>
            </article>

            {/* Feedback */}
            <div className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-5 text-center">
              {feedback === null ? (
                <>
                  <p className="text-sm font-medium">Isso resolveu sua dúvida?</p>
                  <div className="flex gap-3">
                    <button onClick={() => setFeedback("up")} className="btn-ghost px-4 py-2 text-sm">
                      <ThumbsUp className="h-4 w-4" /> Sim
                    </button>
                    <button onClick={() => setFeedback("down")} className="btn-ghost px-4 py-2 text-sm">
                      <ThumbsDown className="h-4 w-4" /> Não
                    </button>
                  </div>
                </>
              ) : feedback === "up" ? (
                <p className="text-sm text-emerald-300">Que bom! Obrigado pelo retorno. 🎉</p>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <p className="text-sm text-foreground/80">Sentimos muito. Vamos te ajudar diretamente:</p>
                  <div className="flex flex-wrap justify-center gap-3">
                    <Link to="/suporte/novo" className="btn-gold px-4 py-2 text-sm">
                      <Plus className="h-4 w-4" /> Abrir ticket
                    </Link>
                    <button type="button" onClick={() => openChat()} className="btn-ghost px-4 py-2 text-sm">
                      <MessageCircle className="h-4 w-4" /> Falar no chat
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
