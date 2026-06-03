import { Hexagon, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao entrar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Entrar" subtitle="Bem-vindo de volta ao enxame.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="E-mail" type="email" value={email} onChange={setEmail} placeholder="voce@email.com" />
        <Field label="Senha" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button disabled={loading} className="btn-gold mt-2 py-3.5 text-base disabled:opacity-60">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Entrar"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Não tem conta? <Link to="/cadastrar" className="text-gold-300 hover:underline">Criar conta</Link>
      </p>
    </AuthShell>
  );
}

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-28">
      <div className="glass w-full max-w-md rounded-[2rem] p-8 sm:p-10">
        <Link to="/" className="mb-6 flex items-center gap-2">
          <Hexagon className="h-8 w-8 text-gold-400" strokeWidth={1.5} />
          <span className="font-display text-xl font-bold">HIVEE</span>
        </Link>
        <h1 className="font-display text-3xl font-bold">{title}</h1>
        <p className="mt-1 mb-7 text-muted-foreground">{subtitle}</p>
        {children}
      </div>
    </div>
  );
}

export function Field({
  label, type = "text", value, onChange, placeholder,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-foreground/80">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-foreground placeholder:text-muted-foreground focus:border-gold-500/50 focus:outline-none"
      />
    </label>
  );
}
