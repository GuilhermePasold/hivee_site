import { AnimatePresence, motion } from "framer-motion";
import { LogOut, Menu, User as UserIcon, X } from "lucide-react";
import { useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import NotificationBell from "@/components/NotificationBell";

const BASE_LINKS = [
  { label: "Início", to: "/" },
  { label: "Buscar", to: "/buscar" },
  { label: "Meu Perfil", to: "/minha-conta" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ left: 0, width: 0, opacity: 0 });

  // A aba "Painel" só aparece para quem é PRESTADOR VERIFICADO (aprovado).
  // "Ajuda" (Central de Ajuda) só para usuários logados — toda a área de suporte
  // exige autenticação.
  const isVerifiedProvider = user?.is_provider && user?.provider_status === "approved";
  const LINKS = [
    ...BASE_LINKS,
    ...(isVerifiedProvider ? [{ label: "Painel", to: "/painel" }] : []),
    ...(user ? [{ label: "Ajuda", to: "/ajuda" }] : []),
  ];

  // Hide navbar over the cinematic hero on the home route (it has its own scene).
  const onHome = location.pathname === "/";

  return (
    <motion.header
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay: onHome ? 0.4 : 0, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-x-0 top-4 z-50 px-4"
    >
      <nav className="glass mx-auto flex max-w-5xl items-center justify-between gap-3 rounded-full px-3 py-2">
        <Link to="/" className="flex items-center pl-1">
          <img src="/hivee_logo.png" alt="HIVEE" className="h-14 w-auto" />
        </Link>

        {/* Center links with sliding cursor */}
        <ul
          className="relative hidden items-center md:flex"
          onMouseLeave={() => setPos((p) => ({ ...p, opacity: 0 }))}
        >
          {LINKS.map((l) => (
            <Tab key={l.to} to={l.to} setPos={setPos} active={location.pathname === l.to}>
              {l.label}
            </Tab>
          ))}
          <motion.li
            animate={pos}
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            className="absolute z-0 h-9 rounded-full bg-gold-500/20"
          />
        </ul>

        {/* Right: auth */}
        <div className="flex items-center gap-2">
          {user ? (
            <div className="flex items-center gap-2">
              <NotificationBell />
              <Link
                to="/minha-conta"
                className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-foreground/80 transition-colors hover:border-gold-500/40 hover:text-foreground sm:flex"
              >
                <UserIcon className="h-4 w-4 text-gold-400" />
                {user.first_name || user.email.split("@")[0]}
              </Link>
              <button
                onClick={() => { logout(); navigate("/"); }}
                aria-label="Sair"
                className="btn-ghost h-9 w-9 rounded-full"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <Link to="/entrar" className="btn-ghost hidden px-4 py-2 text-sm sm:inline-flex">
                Entrar
              </Link>
              <Link to="/cadastrar" className="btn-gold px-4 py-2 text-sm">
                Criar conta
              </Link>
            </>
          )}
          <button
            aria-label="Menu"
            onClick={() => setOpen((v) => !v)}
            className="btn-ghost h-9 w-9 rounded-full md:hidden"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="glass mx-auto mt-2 max-w-5xl overflow-hidden rounded-3xl p-2 md:hidden"
          >
            {LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                onClick={() => setOpen(false)}
                className="block rounded-2xl px-4 py-3 text-base text-foreground/80 transition-colors hover:bg-white/8 hover:text-foreground"
              >
                {l.label}
              </Link>
            ))}
            {user && (
              <>
                <Link
                  to="/notificacoes"
                  onClick={() => setOpen(false)}
                  className="block rounded-2xl px-4 py-3 text-base text-foreground/80 transition-colors hover:bg-white/8 hover:text-foreground"
                >
                  Notificações
                </Link>
                <Link
                  to="/suporte/tickets"
                  onClick={() => setOpen(false)}
                  className="block rounded-2xl px-4 py-3 text-base text-foreground/80 transition-colors hover:bg-white/8 hover:text-foreground"
                >
                  Meus tickets
                </Link>
              </>
            )}
            {!user && (
              <Link to="/entrar" onClick={() => setOpen(false)} className="block rounded-2xl px-4 py-3 text-base text-foreground/80">
                Entrar
              </Link>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}

function Tab({
  children,
  to,
  setPos,
  active,
}: {
  children: React.ReactNode;
  to: string;
  setPos: (p: { left: number; width: number; opacity: number }) => void;
  active: boolean;
}) {
  const ref = useRef<HTMLLIElement>(null);
  return (
    <li
      ref={ref}
      onMouseEnter={() => {
        if (!ref.current) return;
        const { width } = ref.current.getBoundingClientRect();
        setPos({ width, opacity: 1, left: ref.current.offsetLeft });
      }}
      className="relative z-10"
    >
      <Link
        to={to}
        className={`block px-4 py-1.5 text-sm transition-colors ${
          active ? "text-gold-300" : "text-foreground/70 hover:text-foreground"
        }`}
      >
        {children}
      </Link>
    </li>
  );
}
