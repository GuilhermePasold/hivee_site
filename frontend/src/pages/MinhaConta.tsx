import { BadgeCheck, LogOut, Mail, User as UserIcon, Wrench } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function MinhaConta() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return <div className="min-h-screen px-6 pt-28"><div className="surface mx-auto h-64 max-w-xl animate-pulse rounded-3xl" /></div>;
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 py-28">
        <div className="glass w-full max-w-md rounded-[2rem] p-10 text-center">
          <UserIcon className="mx-auto h-10 w-10 text-gold-400" />
          <h1 className="mt-4 text-2xl font-bold">Entre na sua conta</h1>
          <p className="mt-2 text-muted-foreground">Acesse seu perfil, buscas e contratações.</p>
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
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">Meu perfil</h1>

        <div className="surface mt-8 rounded-3xl p-6 sm:p-8">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-gold-500/30 bg-gold-500/10 text-2xl font-bold text-gold-300">
              {(user.first_name || user.email)[0]?.toUpperCase()}
            </div>
            <div>
              <p className="flex items-center gap-2 text-xl font-bold">
                {user.first_name || "Sua conta"}
                {user.is_provider && <BadgeCheck className="h-5 w-5 text-gold-400" />}
              </p>
              <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Mail className="h-4 w-4" /> {user.email}
              </p>
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-foreground/75">
            {user.is_provider
              ? "Você tem um perfil de profissional ativo na HIVEE."
              : "Conta de cliente. Você pode contratar profissionais e, quando quiser, criar seu próprio perfil de profissional."}
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            {user.is_provider && user.provider_slug ? (
              <Link to={`/prestador/${user.provider_slug}`} className="btn-gold flex-1 py-3">
                <BadgeCheck className="h-4 w-4" /> Ver meu perfil público
              </Link>
            ) : (
              <Link to="/buscar" className="btn-gold flex-1 py-3">Buscar profissionais</Link>
            )}
            {!user.is_provider && (
              <Link to="/sou-prestador" className="btn-ghost flex-1 py-3">
                <Wrench className="h-4 w-4" /> Tornar-se profissional
              </Link>
            )}
            <button onClick={() => { logout(); navigate("/"); }} className="btn-ghost py-3 sm:px-5">
              <LogOut className="h-4 w-4" /> Sair
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
