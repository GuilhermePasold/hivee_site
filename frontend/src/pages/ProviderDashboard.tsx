import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Camera, CalendarDays, Check, Clock, Hash, ImagePlus, Loader2, Lock,
  Plus, Save, Trash2,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Field } from "@/pages/Login";
import Avatar from "@/components/ui/Avatar";
import GlassSelect from "@/components/ui/GlassSelect";
import TagInput from "@/components/ui/TagInput";
import type { AvailabilitySlot, GalleryImage, Provider } from "@/types";

const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const emptySlot = (): AvailabilitySlot => ({ day_of_week: 0, start_time: "08:00", end_time: "18:00" });

export default function ProviderDashboard() {
  const { user, loading: authLoading, refresh } = useAuth();
  const navigate = useNavigate();
  const slug = user?.provider_slug ?? "";

  const [provider, setProvider] = useState<Provider | null>(null);
  const [loading, setLoading] = useState(true);

  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [rate, setRate] = useState("");
  const [responseTime, setResponseTime] = useState("");
  const [availability, setAvailability] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [gallery, setGallery] = useState<GalleryImage[]>([]);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const avatarInput = useRef<HTMLInputElement>(null);
  const photoInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    api
      .provider(slug)
      .then((p) => {
        setProvider(p);
        setHeadline(p.headline);
        setBio(p.bio);
        setRate(String(p.hourly_rate));
        setResponseTime(p.response_time);
        setAvailability(p.availability);
        setTags((p.tags ?? []).map((t) => t.name));
        setSlots(p.availability_slots ?? []);
        setGallery(p.gallery ?? []);
        setAvatarUrl(p.avatar || p.avatar_url || null);
      })
      .catch(() => setError("Não foi possível carregar seu perfil."))
      .finally(() => setLoading(false));
  }, [slug]);

  if (authLoading) return null;

  if (!user) {
    return <Guard title="Entre na sua conta" text="Você precisa estar logado." cta="Entrar" to="/entrar" />;
  }
  if (user.provider_status !== "approved" || !slug) {
    return (
      <Guard
        title="Área exclusiva de profissionais"
        text="Este painel fica disponível quando seu perfil de profissional é aprovado."
        cta={user.is_provider ? "Ver minha conta" : "Tornar-se profissional"}
        to={user.is_provider ? "/minha-conta" : "/sou-prestador"}
      />
    );
  }

  function updateSlot(i: number, field: keyof AvailabilitySlot, v: number | string) {
    setSlots((prev) => prev.map((s, idx) => (idx === i ? { ...s, [field]: v } : s)));
  }

  async function onAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !slug) return;
    setUploadingAvatar(true);
    setAvatarUrl(URL.createObjectURL(file));
    try {
      const res = await api.uploadAvatar(slug, file);
      setAvatarUrl(res.avatar_url);
      refresh?.();
    } catch {
      setError("Falha ao enviar a foto de perfil.");
    } finally {
      setUploadingAvatar(false);
    }
  }

  async function onPhotoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !slug) return;
    setUploadingPhoto(true);
    setError("");
    try {
      const img = await api.addGalleryImage(slug, file, "");
      setGallery((g) => [img, ...g]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar a foto.");
    } finally {
      setUploadingPhoto(false);
      if (photoInput.current) photoInput.current.value = "";
    }
  }

  async function removePhoto(id: number) {
    setGallery((g) => g.filter((x) => x.id !== id));
    if (slug) await api.deleteGalleryImage(slug, id).catch(() => undefined);
  }

  async function save() {
    if (!slug) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const updated = await api.updateProvider(slug, {
        headline: headline.trim(),
        bio: bio.trim(),
        hourly_rate: Number(rate) || 0,
        response_time: responseTime.trim(),
        availability: availability.trim(),
        tags,
        availability_slots: slots,
      });
      setProvider(updated);
      setTags((updated.tags ?? []).map((t) => t.name));
      setSlots(updated.availability_slots ?? []);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  const completeness = provider?.profile_completeness ?? 0;

  return (
    <div className="min-h-screen px-6 pb-28 pt-28">
      <div className="mx-auto max-w-4xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-4xl font-bold sm:text-5xl">
              Painel do <span className="text-gold">profissional</span>
            </h1>
            <p className="mt-2 text-muted-foreground">
              Edite seu perfil público, agenda e portfólio. As mudanças vão direto para a HIVEE.
            </p>
          </div>
          <Link to={`/prestador/${slug}`} className="btn-ghost px-5 py-2.5 text-sm">
            Ver meu perfil público
          </Link>
        </div>

        {loading ? (
          <div className="surface mt-8 h-96 animate-pulse rounded-3xl opacity-60" />
        ) : (
          <div className="mt-8 flex flex-col gap-6">
            {/* Completeness + avatar */}
            <section className="surface rounded-3xl p-6 sm:p-8">
              <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
                <div className="relative shrink-0">
                  <Avatar src={avatarUrl} alt={provider?.name || "Você"} size={104} className="rounded-3xl border-2 border-white/20 object-cover" />
                  <button
                    type="button"
                    onClick={() => avatarInput.current?.click()}
                    className="absolute -bottom-2 -right-2 flex h-9 w-9 items-center justify-center rounded-full border border-gold-500/50 bg-[#15151a] text-gold-300 transition-colors hover:bg-gold-500/20"
                    aria-label="Mudar foto"
                  >
                    {uploadingAvatar ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
                  </button>
                  <input ref={avatarInput} type="file" accept="image/*" onChange={onAvatarChange} className="hidden" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-foreground/80">Perfil completo</p>
                    <span className="font-display text-lg font-bold text-gold-300">{completeness}%</span>
                  </div>
                  <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-gold-500 to-gold-300 transition-all duration-500"
                      style={{ width: `${completeness}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Perfis completos (foto, bio, 3+ tags, agenda, portfólio e localização) aparecem mais e convertem melhor.
                  </p>
                </div>
              </div>
            </section>

            {/* Basic fields */}
            <section className="surface flex flex-col gap-4 rounded-3xl p-6 sm:p-8">
              <h2 className="font-display text-xl font-semibold">Sobre o serviço</h2>
              <Field label="Título" value={headline} onChange={setHeadline} placeholder="Ex.: Eletricista residencial 24h" />
              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-foreground/80">Sobre você</span>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows={4}
                  placeholder="Conte sua experiência, diferenciais e o que você oferece."
                  className="rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
                />
              </label>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Valor por hora (R$)" type="number" value={rate} onChange={setRate} placeholder="80" />
                <Field label="Tempo de resposta" value={responseTime} onChange={setResponseTime} placeholder="em 1 hora" />
                <Field label="Disponibilidade" value={availability} onChange={setAvailability} placeholder="Disponível esta semana" />
              </div>
            </section>

            {/* Tags */}
            <section className="surface flex flex-col gap-3 rounded-3xl p-6 sm:p-8">
              <div>
                <h2 className="flex items-center gap-2 font-display text-xl font-semibold">
                  <Hash className="h-5 w-5 text-gold-400" /> Serviços oferecidos (tags)
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Além da categoria, descreva o que você faz. Tags ajudam clientes a te achar na busca.
                  Digite e escolha uma existente ou crie a sua.
                </p>
              </div>
              <TagInput value={tags} onChange={setTags} placeholder="Ex.: instalação de chuveiro" />
            </section>

            {/* Availability schedule */}
            <section className="surface flex flex-col gap-3 rounded-3xl p-6 sm:p-8">
              <h2 className="flex items-center gap-2 font-display text-xl font-semibold">
                <CalendarDays className="h-5 w-5 text-gold-400" /> Agenda de disponibilidade
              </h2>
              <p className="-mt-1 text-sm text-muted-foreground">
                Marque os dias e horários que você atende. Aparece no seu perfil para o cliente.
              </p>
              {slots.length === 0 && (
                <p className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-muted-foreground">
                  Nenhum horário cadastrado ainda.
                </p>
              )}
              {slots.map((slot, i) => (
                <div key={i} className="flex flex-wrap items-end gap-2 rounded-2xl border border-white/12 bg-white/5 p-3">
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-muted-foreground">Dia</span>
                    <GlassSelect
                      value={String(slot.day_of_week)}
                      onChange={(v) => updateSlot(i, "day_of_week", Number(v))}
                      options={DAYS.map((d, idx) => ({ value: String(idx), label: d }))}
                      triggerClassName="py-2 text-sm min-w-[84px]"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-muted-foreground">Início</span>
                    <input type="time" value={slot.start_time} onChange={(e) => updateSlot(i, "start_time", e.target.value)}
                      className="rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-foreground focus:border-gold-500/50 focus:outline-none" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-muted-foreground">Fim</span>
                    <input type="time" value={slot.end_time} onChange={(e) => updateSlot(i, "end_time", e.target.value)}
                      className="rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-foreground focus:border-gold-500/50 focus:outline-none" />
                  </div>
                  <button type="button" onClick={() => setSlots((p) => p.filter((_, idx) => idx !== i))} className="p-2 text-rose-400 hover:text-rose-300">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <button type="button" onClick={() => setSlots((p) => [...p, emptySlot()])} className="mt-1 flex items-center gap-2 self-start text-sm text-gold-400 hover:text-gold-300">
                <Plus className="h-4 w-4" /> Adicionar horário
              </button>
            </section>

            {/* Gallery */}
            <section className="surface flex flex-col gap-3 rounded-3xl p-6 sm:p-8">
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-display text-xl font-semibold">
                  <ImagePlus className="h-5 w-5 text-gold-400" /> Fotos dos serviços
                </h2>
                <span className="text-xs text-muted-foreground">{gallery.length}/12</span>
              </div>
              <p className="-mt-1 text-sm text-muted-foreground">
                Mostre seu trabalho. Essas fotos vão para o seu perfil público.
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {gallery.map((g) => (
                  <div key={g.id} className="group relative aspect-square overflow-hidden rounded-2xl border border-white/10">
                    <img src={g.image_url || ""} alt={g.alt_text || "Serviço"} className="h-full w-full object-cover" />
                    <button
                      type="button"
                      onClick={() => removePhoto(g.id)}
                      aria-label="Remover foto"
                      className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-rose-300 opacity-0 transition-opacity hover:bg-rose-500/30 group-hover:opacity-100"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {gallery.length < 12 && (
                  <button
                    type="button"
                    onClick={() => photoInput.current?.click()}
                    className="flex aspect-square flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-white/20 bg-white/[0.03] text-muted-foreground transition-colors hover:border-gold-500/50 hover:text-gold-300"
                  >
                    {uploadingPhoto ? <Loader2 className="h-6 w-6 animate-spin" /> : <Plus className="h-6 w-6" />}
                    <span className="text-xs">Adicionar</span>
                  </button>
                )}
                <input ref={photoInput} type="file" accept="image/*" onChange={onPhotoUpload} className="hidden" />
              </div>
            </section>

            {error && <p className="text-sm text-rose-400">{error}</p>}

            {/* Save bar */}
            <div className="sticky bottom-4 flex items-center justify-end gap-3">
              {saved && (
                <span className="flex items-center gap-1.5 text-sm text-emerald-400">
                  <Check className="h-4 w-4" /> Salvo!
                </span>
              )}
              <button onClick={save} disabled={saving} className="btn-gold px-7 py-3.5 text-base shadow-xl disabled:opacity-60">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Save className="h-4 w-4" /> Salvar alterações</>}
              </button>
            </div>
            <p className="flex items-center justify-end gap-1.5 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" /> A foto de perfil e as do portfólio são salvas na hora.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function Guard({ title, text, cta, to }: { title: string; text: string; cta: string; to: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-28">
      <div className="glass w-full max-w-md rounded-[2rem] p-10 text-center">
        <Lock className="mx-auto h-10 w-10 text-gold-400" />
        <h1 className="mt-4 font-display text-2xl font-bold">{title}</h1>
        <p className="mt-2 text-muted-foreground">{text}</p>
        <Link to={to} className="btn-gold mt-6 inline-block px-6 py-3">{cta}</Link>
      </div>
    </div>
  );
}
