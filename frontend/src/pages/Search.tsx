import { MapPin, Search as SearchIcon, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import type { Category, City, Provider } from "@/types";
import ProviderCard from "@/components/ProviderCard";
import Icon from "@/components/ui/Icon";
import GlassSelect from "@/components/ui/GlassSelect";

const SORTS = [
  { value: "", label: "Relevância" },
  { value: "-rating", label: "Melhor avaliado" },
  { value: "hourly_rate", label: "Menor preço" },
];

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [categories, setCategories] = useState<Category[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const q = params.get("q") ?? "";
  const city = params.get("cidade") ?? "";
  const category = params.get("categoria") ?? "";
  const ordering = params.get("ordenar") ?? "";

  const [queryInput, setQueryInput] = useState(q);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => undefined);
    api.cities().then(setCities).catch(() => undefined);
  }, []);

  useEffect(() => {
    setQueryInput(q);
  }, [q]);

  useEffect(() => {
    // The search only runs once a city is confirmed — no city, no (misleading)
    // results. This avoids showing the same providers regardless of location.
    setLoading(true);
    const t = setTimeout(() => {
      api
        .providers({ search: q, city, category, ordering, page_size: 24 })
        .then((r) => {
          setProviders(r.results);
          setCount(r.count);
        })
        .catch(() => {
          setProviders([]);
          setCount(0);
        })
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q, city, category, ordering]);

  function update(patch: Record<string, string>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    setParams(next, { replace: true });
  }

  const activeCategory = useMemo(
    () => categories.find((c) => c.slug === category),
    [categories, category],
  );

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-6xl">
        {/* Heading */}
        <h1 className="font-display text-5xl font-bold leading-tight sm:text-6xl">
          Encontre seu <span className="text-gold">profissional</span>
        </h1>

        {/* Search bar */}
        <div className="glass mt-8 flex flex-col gap-2 rounded-3xl p-2 sm:flex-row sm:items-center sm:rounded-full">
          <div className="flex flex-1 items-center gap-2 px-3">
            <SearchIcon className="h-5 w-5 shrink-0 text-gold-400" />
            <input
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && update({ q: queryInput })}
              placeholder="O que você precisa? (ex.: eletricista)"
              className="w-full bg-transparent py-2.5 text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
          </div>
          <div className="hidden h-8 w-px bg-white/12 sm:block" />
          <div className="flex flex-1 items-center gap-2 px-3">
            <MapPin className="h-5 w-5 shrink-0 text-gold-400" />
            <GlassSelect
              value={city}
              onChange={(v) => update({ cidade: v })}
              placeholder="Todas as cidades"
              className="flex-1"
              triggerClassName="border-0 bg-transparent px-0 py-2.5 hover:border-0 focus:border-0"
              options={[
                { value: "", label: "Todas as cidades" },
                ...cities.map((c) => ({
                  value: c.city,
                  label: `${c.city}, ${c.state} (${c.count})`,
                })),
              ]}
            />
          </div>
          <button onClick={() => update({ q: queryInput })} className="btn-gold justify-center px-7 py-3 text-base">
            Buscar
          </button>
        </div>

        {/* Category chips */}
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => update({ categoria: "" })}
            className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
              !category ? "border-gold-500/50 bg-gold-500/15 text-gold-200" : "border-white/12 bg-white/5 text-foreground/70 hover:text-foreground"
            }`}
          >
            Todas
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => update({ categoria: category === c.slug ? "" : c.slug })}
              className={`flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
                category === c.slug ? "border-gold-500/50 bg-gold-500/15 text-gold-200" : "border-white/12 bg-white/5 text-foreground/70 hover:text-foreground"
              }`}
            >
              <Icon name={c.icon} className="h-3.5 w-3.5" /> {c.name}
            </button>
          ))}
        </div>

        {/* Result bar — only once a city is chosen */}
        {(
          <div className="mt-8 flex flex-col gap-4 border-t border-white/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-lg text-foreground/80">
              {loading ? "Buscando…" : <><span className="font-semibold text-foreground">{count}</span> profissionai{count === 1 ? "" : "s"}</>}
              <span className="text-muted-foreground">{city ? ` em ${city}` : " disponiveis"}</span>
              {activeCategory && <span className="text-muted-foreground"> · {activeCategory.name}</span>}
            </p>
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
              <div className="glass flex items-center gap-1 rounded-full p-1">
                {SORTS.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => update({ ordenar: s.value })}
                    className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
                      ordering === s.value ? "bg-gold-500/20 text-gold-200" : "text-foreground/60 hover:text-foreground"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Active filters */}
        {(q || city || category) && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {q && <Chip onClear={() => update({ q: "" })}>“{q}”</Chip>}
            {city && <Chip onClear={() => update({ cidade: "" })}>{city}</Chip>}
            {activeCategory && <Chip onClear={() => update({ categoria: "" })}>{activeCategory.name}</Chip>}
          </div>
        )}

        {/* Results */}
        <div className="mt-8">
          {loading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="surface h-80 animate-pulse rounded-3xl opacity-60" />
              ))}
            </div>
          ) : providers.length === 0 ? (
            <div className="surface flex flex-col items-center gap-3 rounded-3xl p-16 text-center">
              <p className="font-display text-2xl font-semibold">Nada encontrado</p>
              <p className="max-w-md text-sm text-muted-foreground">
                Tente outra busca, troque a cidade ou limpe os filtros.
              </p>
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {providers.map((p) => (
                <ProviderCard key={p.id} provider={p} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CityPrompt({ cities, onPick }: { cities: City[]; onPick: (city: string) => void }) {
  return (
    <div className="surface flex flex-col items-center gap-6 rounded-3xl p-12 text-center sm:p-16">
      <span className="flex h-16 w-16 items-center justify-center rounded-2xl border border-gold-500/30 bg-gold-500/15">
        <MapPin className="h-8 w-8 text-gold-300" />
      </span>
      <div>
        <p className="font-display text-2xl font-semibold sm:text-3xl">Escolha sua cidade</p>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Selecione uma cidade para ver só os profissionais que realmente atendem perto de você.
        </p>
      </div>
      {cities.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2">
          {cities.slice(0, 8).map((c) => (
            <button
              key={c.city}
              onClick={() => onPick(c.city)}
              className="rounded-full border border-white/12 bg-white/5 px-4 py-2 text-sm text-foreground/80 transition-colors hover:border-gold-500/50 hover:text-gold-200"
            >
              {c.city} <span className="text-muted-foreground">({c.count})</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Chip({ children, onClear }: { children: React.ReactNode; onClear: () => void }) {
  return (
    <span className="glass inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm text-foreground/80">
      {children}
      <button onClick={onClear} aria-label="Remover" className="flex h-5 w-5 items-center justify-center rounded-full hover:bg-white/10">
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}
