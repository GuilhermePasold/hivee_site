import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function Footer() {
  const { user } = useAuth();
  return (
    <footer className="border-t border-white/10 px-4 py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 sm:flex-row">
        <Link to="/" className="flex items-center">
          <img src="/hivee_logo.png" alt="HIVEE" className="h-20 w-auto" />
        </Link>
        <nav className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
          <Link to="/buscar" className="transition-colors hover:text-gold-300">Buscar</Link>
          <Link to="/sou-prestador" className="transition-colors hover:text-gold-300">Sou profissional</Link>
          {/* Suporte só para usuários logados (toda a área exige autenticação). */}
          {user ? (
            <Link to="/ajuda" className="transition-colors hover:text-gold-300">Ajuda</Link>
          ) : (
            <Link to="/entrar" className="transition-colors hover:text-gold-300">Entrar</Link>
          )}
          <a href="#" className="transition-colors hover:text-gold-300">Termos</a>
        </nav>
        <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} HIVEE</p>
      </div>
    </footer>
  );
}
