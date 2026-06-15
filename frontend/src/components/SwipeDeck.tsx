import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { animate, motion, useMotionValue, useTransform, type PanInfo } from "framer-motion";
import { Heart, X, ExternalLink, Handshake } from "lucide-react";
import { Card } from "@/components/ui/stacked-cards-interaction";
import RecCard from "@/components/RecCard";
import type { Recommendation, SwipeAction } from "@/types";

const THRESHOLD = 120; // px de arrasto para confirmar a decisão

interface SwipeDeckProps {
  recs: Recommendation[];
  onSwipe: (rec: Recommendation, action: SwipeAction) => void;
}

// Deck estilo Tinder: arraste o card (ou use os botões) para curtir/passar.
// Reutiliza o cartão de vidro (Card) e o conteúdo visual de recomendação (RecCard).
export default function SwipeDeck({ recs, onSwipe }: SwipeDeckProps) {
  const [index, setIndex] = useState(0);
  const [leaving, setLeaving] = useState(false);
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-220, 220], [-18, 18]);
  const likeOpacity = useTransform(x, [30, 130], [0, 1]);
  const nopeOpacity = useTransform(x, [-130, -30], [1, 0]);

  // Recomeça do topo sempre que o deck é recarregado.
  useEffect(() => {
    setIndex(0);
    x.set(0);
  }, [recs, x]);

  const current = recs[index];
  const behind = recs[index + 1];

  async function fling(action: SwipeAction) {
    if (!current || leaving) return;
    setLeaving(true);
    const dir = action === "like" ? 1 : -1;
    await animate(x, dir * 700, { duration: 0.32, ease: [0.16, 1, 0.3, 1] }).finished;
    onSwipe(current, action);
    x.jump(0); // recoloca instantaneamente para o próximo card
    setIndex((i) => i + 1);
    setLeaving(false);
  }

  function handleDragEnd(_: unknown, info: PanInfo) {
    if (info.offset.x > THRESHOLD) fling("like");
    else if (info.offset.x < -THRESHOLD) fling("dislike");
    else animate(x, 0, { type: "spring", stiffness: 300, damping: 26 });
  }

  if (!current) {
    return (
      <div className="surface flex h-[420px] w-full max-w-[360px] flex-col items-center justify-center gap-3 rounded-3xl p-8 text-center">
        <Handshake className="h-9 w-9 text-gold-400" />
        <p className="font-display text-xl font-semibold">Você viu todo mundo!</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Não há mais recomendações por agora. Busque mais profissionais e volte:
          quanto mais você usa, melhores ficam as indicações.
        </p>
        <Link to="/buscar" className="btn-gold mt-2 px-5 py-2.5 text-sm">
          Buscar profissionais
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-7">
      <div className="relative h-[420px] w-[340px]">
        {/* Card de trás (próximo da fila), dá profundidade ao deck */}
        {behind && (
          <div className="absolute inset-0 scale-[0.94] opacity-50">
            <Card>
              <RecCard rec={behind} />
            </Card>
          </div>
        )}

        {/* Card do topo, arrastável */}
        <motion.div
          key={current.id}
          className="absolute inset-0 cursor-grab touch-none active:cursor-grabbing"
          style={{ x, rotate }}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.7}
          onDragEnd={handleDragEnd}
          initial={{ scale: 0.96, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 320, damping: 26 }}
        >
          <Card>
            <div className="relative h-full">
              <RecCard rec={current} />
              {/* Carimbos de feedback durante o arrasto */}
              <motion.span
                style={{ opacity: likeOpacity }}
                className="pointer-events-none absolute left-5 top-5 rotate-[-12deg] rounded-xl border-2 border-emerald-400 px-3 py-1 text-lg font-extrabold uppercase tracking-wider text-emerald-400"
              >
                Curtir
              </motion.span>
              <motion.span
                style={{ opacity: nopeOpacity }}
                className="pointer-events-none absolute right-5 top-5 rotate-[12deg] rounded-xl border-2 border-rose-400 px-3 py-1 text-lg font-extrabold uppercase tracking-wider text-rose-400"
              >
                Passar
              </motion.span>
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Controles */}
      <div className="flex items-center gap-5">
        <button
          type="button"
          onClick={() => fling("dislike")}
          aria-label="Passar"
          className="flex h-14 w-14 items-center justify-center rounded-full border border-white/15 bg-white/5 text-rose-400 transition-colors hover:border-rose-400/60 hover:bg-rose-500/10"
        >
          <X className="h-6 w-6" />
        </button>
        <Link
          to={`/prestador/${current.slug}`}
          aria-label="Ver perfil"
          className="flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-white/5 text-foreground/70 transition-colors hover:border-gold-500/50 hover:text-gold-300"
        >
          <ExternalLink className="h-5 w-5" />
        </Link>
        <button
          type="button"
          onClick={() => fling("like")}
          aria-label="Curtir"
          className="flex h-14 w-14 items-center justify-center rounded-full border border-gold-500/40 bg-gold-500/15 text-gold-300 transition-transform hover:scale-105 hover:bg-gold-500/25"
        >
          <Heart className="h-6 w-6 fill-gold-400/30" />
        </button>
      </div>
      <p className="text-xs text-muted-foreground">
        Arraste o card ou use os botões · curtir salva nos favoritos
      </p>
    </div>
  );
}
