import { MapPin, Menu, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import Icon from "@/components/ui/Icon";
import type { Category } from "@/types";

// A real, working mini search living inside the hero phone — the inputs and
// buttons actually run the same search as the site (navigate to /buscar).
export default function PhoneApp() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [cats, setCats] = useState<Category[]>([]);

  useEffect(() => {
    api.categories().then(setCats).catch(() => undefined);
  }, []);

  const go = (params: string) => navigate("/buscar" + params);

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-[#16120b] to-[#0c0a06] px-4 pb-4 pt-9 text-left">
      <div className="flex items-center justify-between">
        <img
          src="/hivee_logo.png"
          alt="HIVEE"
          className="h-6 w-auto animate-in fade-in zoom-in duration-700"
        />
        <Menu className="h-4 w-4 text-foreground/60" />
      </div>

      <h3 className="mt-6 text-2xl font-extrabold leading-[1.05] tracking-tight">
        Encontre seu
        <br />
        <span className="text-gold">profissional</span>
      </h3>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          go(q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "");
        }}
        className="surface mt-3 rounded-2xl p-2"
      >
        <div className="flex items-center gap-1.5 px-1.5">
          <Search className="h-3.5 w-3.5 shrink-0 text-gold-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="O que você precisa?"
            className="w-full bg-transparent py-1.5 text-xs placeholder:text-foreground/40 focus:outline-none"
          />
        </div>
        <div className="mt-1.5 flex items-center gap-1.5 border-t border-white/10 px-1.5 pt-1.5">
          <MapPin className="h-3.5 w-3.5 shrink-0 text-gold-400" />
          <span className="text-[11px] text-foreground/55">Todas as cidades</span>
        </div>
        <button type="submit" className="btn-gold mt-2 w-full justify-center py-2 text-xs">
          Buscar
        </button>
      </form>

      <p className="mb-1.5 mt-3 text-[10px] uppercase tracking-wider text-foreground/40">
        Categorias
      </p>
      <div className="flex flex-wrap gap-1.5 overflow-hidden">
        {cats.slice(0, 8).map((c) => (
          <button
            key={c.id}
            onClick={() => go(`?categoria=${c.slug}`)}
            className="flex items-center gap-1 rounded-full border border-white/12 bg-white/5 px-2 py-1 text-[10px] text-foreground/75 transition-colors hover:border-gold-500/40 hover:text-gold-200"
          >
            <Icon name={c.icon} className="h-3 w-3 text-gold-300" /> {c.name}
          </button>
        ))}
      </div>
    </div>
  );
}
