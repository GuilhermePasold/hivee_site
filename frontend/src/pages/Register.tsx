import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { AuthShell, Field } from "@/pages/Login";

function validateCPF(cpf: string): boolean {
  const n = cpf.replace(/\D/g, "");
  if (n.length !== 11 || n === n[0].repeat(11)) return false;
  for (let i = 9; i <= 10; i++) {
    let soma = 0;
    for (let j = 0; j < i; j++) soma += parseInt(n[j]) * (i + 1 - j);
    const dig = (soma * 10 % 11) % 10;
    if (parseInt(n[i]) !== dig) return false;
  }
  return true;
}

function maskCPF(v: string) {
  const n = v.replace(/\D/g, "").slice(0, 11);
  return n.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cpf, setCpf] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (cpf && !validateCPF(cpf)) {
      setError("CPF inválido. Verifique os dígitos.");
      return;
    }
    setLoading(true);
    try {
      await register(name, email, password, cpf || undefined);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar conta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Criar conta" subtitle="Entre para o enxame em 30 segundos.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Nome" value={name} onChange={setName} placeholder="Seu nome" />
        <Field label="E-mail" type="email" value={email} onChange={setEmail} placeholder="voce@email.com" />
        <Field label="CPF" value={cpf} onChange={(v) => setCpf(maskCPF(v))} placeholder="000.000.000-00" />
        <Field label="Senha" type="password" value={password} onChange={setPassword} placeholder="mínimo 6 caracteres" />
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button disabled={loading} className="btn-gold mt-2 py-3.5 text-base disabled:opacity-60">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Criar conta"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Já tem conta? <Link to="/entrar" className="text-gold-300 hover:underline">Entrar</Link>
      </p>
    </AuthShell>
  );
}
