import { Hexagon } from "lucide-react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 px-4 py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 sm:flex-row">
        <Link to="/" className="flex items-center gap-2">
          <Hexagon className="h-7 w-7 text-gold-400" strokeWidth={1.5} />
          <span className="font-display text-xl font-bold">HIVEE</span>
        </Link>
        <nav className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
          <Link to="/buscar" className="transition-colors hover:text-gold-300">Buscar</Link>
          <Link to="/sou-prestador" className="transition-colors hover:text-gold-300">Sou profissional</Link>
          <Link to="/entrar" className="transition-colors hover:text-gold-300">Entrar</Link>
          <a href="#" className="transition-colors hover:text-gold-300">Termos</a>
        </nav>
        <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} HIVEE</p>
      </div>
    </footer>
  );
}
