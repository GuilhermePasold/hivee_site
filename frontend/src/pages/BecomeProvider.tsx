import { Camera, Loader2, Lock, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { searchAddress } from "@/lib/geocode";
import { Field } from "@/pages/Login";
import GlassSelect from "@/components/ui/GlassSelect";
import type { AvailabilitySlot, Category, City } from "@/types";

const UF_LIST = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
  "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
  "SP", "SE", "TO",
];

const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function emptySlot(): AvailabilitySlot {
  return { day_of_week: 0, start_time: "08:00", end_time: "18:00" };
}

export default function BecomeProvider() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState<Category[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [catLoading, setCatLoading] = useState(true);
  const [cityLoading, setCityLoading] = useState(true);
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
  });
  const [slots, setSlots] = useState<AvailabilitySlot[]>([emptySlot()]);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.categories().then((d) => { setCategories(d); setCatLoading(false); }).catch(() => setCatLoading(false));
    api.cities().then((d) => { setCities(d); setCityLoading(false); }).catch(() => setCityLoading(false));
  }, []);

  useEffect(() => {
    if (user) setForm((f) => ({ ...f, name: f.name || user.first_name }));
  }, [user]);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function updateSlot(idx: number, field: keyof AvailabilitySlot, value: number | string) {
    setSlots((prev) => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)));
  }

  function addSlot() {
    setSlots((prev) => [...prev, emptySlot()]);
  }

  function removeSlot(idx: number) {
    setSlots((prev) => prev.filter((_, i) => i !== idx));
  }

  function onAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.category) { setError("Selecione uma categoria."); return; }
    setLoading(true);
    try {
      let lat: number | null = null;
      let lng: number | null = null;
      if (form.city) {
        const found = await searchAddress(`${form.neighborhood}, ${form.city}`);
        if (found[0]) {
          lat = found[0].lat;
          lng = found[0].lng;
        }
      }

      const provider = await api.createProvider({
        name: form.name,
        headline: form.headline,
        bio: form.bio,
        category: form.category,
        hourly_rate: Number(form.hourly_rate),
        city: form.city || undefined,
        neighborhood: form.neighborhood || undefined,
        state: form.state || undefined,
        latitude: lat,
        longitude: lng,
        availability_slots: slots,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      });

      if (avatarFile) {
        await api.uploadAvatar(provider.slug, avatarFile);
      }

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
          Preencha seu perfil. Ele passa por análise e é aprovado por nossa equipe.
        </p>

        <form onSubmit={submit} className="surface mt-8 flex flex-col gap-4 rounded-3xl p-6 sm:p-8">
          <Field label="Nome de exibição" value={form.name} onChange={(v) => set("name", v)} placeholder="Ex.: Marina Alves" />
          <Field label="Título" value={form.headline} onChange={(v) => set("headline", v)} placeholder="Ex.: Eletricista residencial" />

          <Select
            label="Categoria"
            value={form.category}
            onChange={(v) => set("category", v)}
            placeholder={catLoading ? "Carregando…" : "Selecione…"}
            options={categories.map((c) => ({ value: c.slug, label: c.name }))}
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Cidade"
              value={form.city}
              onChange={(v) => set("city", v)}
              placeholder={cityLoading ? "Carregando…" : "Selecione…"}
              options={cities.map((c) => ({ value: c.city, label: `${c.city}, ${c.state}` }))}
            />
            <Field label="Bairro" value={form.neighborhood} onChange={(v) => set("neighborhood", v)} placeholder="Ex.: Pinheiros" />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Estado (UF)"
              value={form.state}
              onChange={(v) => set("state", v)}
              options={UF_LIST.map((uf) => ({ value: uf, label: uf }))}
            />
            <Field label="Valor por hora (R$)" type="number" value={form.hourly_rate} onChange={(v) => set("hourly_rate", v)} placeholder="80" />
          </div>

          {/* Availability - mini agenda */}
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-foreground/80">Horários disponíveis</span>
            {slots.map((slot, i) => (
              <div key={i} className="flex flex-wrap items-end gap-2 rounded-2xl border border-white/12 bg-white/5 p-3">
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Dia</span>
                  <GlassSelect
                    value={String(slot.day_of_week)}
                    onChange={(v) => updateSlot(i, "day_of_week", Number(v))}
                    options={DAYS.map((d, idx) => ({ value: String(idx), label: d }))}
                    triggerClassName="py-2 text-sm min-w-[80px]"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Início</span>
                  <input
                    type="time"
                    value={slot.start_time}
                    onChange={(e) => updateSlot(i, "start_time", e.target.value)}
                    className="rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-foreground focus:border-gold-500/50 focus:outline-none"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Fim</span>
                  <input
                    type="time"
                    value={slot.end_time}
                    onChange={(e) => updateSlot(i, "end_time", e.target.value)}
                    className="rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-foreground focus:border-gold-500/50 focus:outline-none"
                  />
                </div>
                {slots.length > 1 && (
                  <button type="button" onClick={() => removeSlot(i)} className="p-2 text-rose-400 hover:text-rose-300">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
            <button type="button" onClick={addSlot} className="flex items-center gap-2 text-sm text-gold-400 hover:text-gold-300 mt-1">
              <Plus className="h-4 w-4" /> Adicionar horário
            </button>
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

          {/* Photo upload */}
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-foreground/80">Sua foto</span>
            <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-white/20 bg-white/5 px-4 py-4 transition-colors hover:border-gold-500/50">
              {avatarPreview ? (
                <img src={avatarPreview} alt="Preview" className="h-14 w-14 rounded-xl object-cover" />
              ) : (
                <Camera className="h-8 w-8 text-muted-foreground" />
              )}
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground/80">{avatarFile ? avatarFile.name : "Clique para escolher uma foto"}</p>
                <p className="text-xs text-muted-foreground">PNG, JPG. Máx 5MB.</p>
              </div>
              <input type="file" accept="image/*" onChange={onAvatarChange} className="hidden" />
            </label>
          </div>

          {error && <p className="text-sm text-rose-400">{error}</p>}

          <button disabled={loading} className="btn-gold mt-2 py-3.5 text-base disabled:opacity-60">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Enviar para análise"}
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
