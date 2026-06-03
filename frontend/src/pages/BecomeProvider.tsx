import { Loader2, Lock } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { searchAddress } from "@/lib/geocode";
import { Field } from "@/pages/Login";
import GlassSelect from "@/components/ui/GlassSelect";
import type { Category, City } from "@/types";

const RESPONSE = ["em poucos minutos", "em 15 min", "em 1 hora", "no mesmo dia"];
const AVAIL = ["Disponível hoje", "Disponível esta semana", "Agenda aberta", "Sob agendamento"];

export default function BecomeProvider() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState<Category[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [form, setForm] = useState({
    name: "",
    headline: "",
    category: "",
    city: "",
    neighborhood: "",
    state: "SP",
    hourly_rate: "80",
    bio: "",
    skills: "",
    response_time: RESPONSE[2],
    availability: AVAIL[1],
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => undefined);
    api.cities().then(setCities).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (user) setForm((f) => ({ ...f, name: f.name || user.first_name }));
  }, [user]);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // Resolve coordinates for the chosen city/neighborhood via OpenStreetMap.
      let lat = -23.5613;
      let lng = -46.6565;
      const found = await searchAddress(`${form.neighborhood}, ${form.city}`);
      if (found[0]) {
        lat = found[0].lat;
        lng = found[0].lng;
      }
      const provider = await api.createProvider({
        name: form.name,
        headline: form.headline,
        bio: form.bio,
        category: form.category,
        hourly_rate: Number(form.hourly_rate),
        city: form.city,
        neighborhood: form.neighborhood,
        state: form.state,
        latitude: lat,
        longitude: lng,
        response_time: form.response_time,
        availability: form.availability,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      });
      navigate(`/prestador/${provider.slug}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao cadastrar");
    } finally {
      setLoading(false);
    }
  }

  if (authLoading) return null;

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 py-28">
        <div className="glass w-full max-w-md rounded-[2rem] p-10 text-center">
          <Lock className="mx-auto h-10 w-10 text-gold-400" />
          <h1 className="mt-4 font-display text-2xl font-bold">Entre para se cadastrar</h1>
          <p className="mt-2 text-muted-foreground">
            Você precisa de uma conta para criar seu perfil de profissional.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Link to="/entrar" className="btn-gold py-3">Entrar</Link>
            <Link to="/cadastrar" className="btn-ghost py-3">Criar conta</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 pb-24 pt-28">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-4xl font-bold sm:text-5xl">
          Vire um <span className="text-gold">profissional HIVEE</span>
        </h1>
        <p className="mt-3 text-muted-foreground">
          Preencha seu perfil. Ele aparece na busca e no mapa para clientes da sua região.
        </p>

        <form onSubmit={submit} className="surface mt-8 flex flex-col gap-4 rounded-3xl p-6 sm:p-8">
          <Field label="Nome de exibição" value={form.name} onChange={(v) => set("name", v)} placeholder="Ex.: Marina Alves" />
          <Field label="Título" value={form.headline} onChange={(v) => set("headline", v)} placeholder="Ex.: Eletricista residencial" />

          <Select
            label="Categoria"
            value={form.category}
            onChange={(v) => set("category", v)}
            placeholder="Selecione…"
            options={categories.map((c) => ({ value: c.slug, label: c.name }))}
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Cidade"
              value={form.city}
              onChange={(v) => set("city", v)}
              placeholder="Selecione…"
              options={cities.map((c) => ({ value: c.city, label: `${c.city}, ${c.state}` }))}
            />
            <Field label="Bairro" value={form.neighborhood} onChange={(v) => set("neighborhood", v)} placeholder="Ex.: Pinheiros" />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Estado (UF)" value={form.state} onChange={(v) => set("state", v)} placeholder="SP" />
            <Field label="Valor por hora (R$)" type="number" value={form.hourly_rate} onChange={(v) => set("hourly_rate", v)} placeholder="80" />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select label="Tempo de resposta" value={form.response_time} onChange={(v) => set("response_time", v)} options={RESPONSE.map((r) => ({ value: r, label: r }))} />
            <Select label="Disponibilidade" value={form.availability} onChange={(v) => set("availability", v)} options={AVAIL.map((a) => ({ value: a, label: a }))} />
          </div>

          <Field label="Especialidades (separadas por vírgula)" value={form.skills} onChange={(v) => set("skills", v)} placeholder="Instalação, Tomadas, Chuveiro" />

          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-foreground/80">Sobre você</span>
            <textarea
              value={form.bio}
              onChange={(e) => set("bio", e.target.value)}
              rows={4}
              placeholder="Conte sua experiência, diferenciais e o que você oferece."
              className="rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
            />
          </label>

          {error && <p className="text-sm text-rose-400">{error}</p>}

          <button disabled={loading} className="btn-gold mt-2 py-3.5 text-base disabled:opacity-60">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Publicar meu perfil"}
          </button>
        </form>
      </div>
    </div>
  );
}

function Select({
  label, value, onChange, options, placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-foreground/80">{label}</span>
      <GlassSelect value={value} onChange={onChange} options={options} placeholder={placeholder} />
    </div>
  );
}
