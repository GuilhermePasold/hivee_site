import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import "./index.css";
import { AuthProvider } from "@/context/AuthContext";
import { NotificationsProvider } from "@/context/NotificationsContext";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import Search from "@/pages/Search";
import Recommended from "@/pages/Recommended";
import ProviderProfile from "@/pages/ProviderProfile";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import BecomeProvider from "@/pages/BecomeProvider";
import MinhaConta from "@/pages/MinhaConta";
import ProviderDashboard from "@/pages/ProviderDashboard";
import Notificacoes from "@/pages/Notificacoes";
import Ajuda from "@/pages/Ajuda";
import ArtigoAjuda from "@/pages/ArtigoAjuda";
import MeusTickets from "@/pages/MeusTickets";
import DetalheTicket from "@/pages/DetalheTicket";
import NovoTicket from "@/pages/NovoTicket";

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="font-display text-6xl font-bold text-gold">404</h1>
      <p className="text-muted-foreground">Essa página não existe.</p>
      <Link to="/" className="btn-gold px-6 py-3">Voltar ao início</Link>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <NotificationsProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Home />} />
              <Route path="/buscar" element={<Search />} />
              <Route path="/recomendados" element={<Recommended />} />
              <Route path="/prestador/:slug" element={<ProviderProfile />} />
              <Route path="/sou-prestador" element={<BecomeProvider />} />
              <Route path="/minha-conta" element={<MinhaConta />} />
              <Route path="/notificacoes" element={<Notificacoes />} />
              <Route path="/painel" element={<ProviderDashboard />} />
              <Route path="/ajuda" element={<Ajuda />} />
              <Route path="/ajuda/:slug" element={<ArtigoAjuda />} />
              <Route path="/suporte/tickets" element={<MeusTickets />} />
              <Route path="/suporte/tickets/:id" element={<DetalheTicket />} />
              <Route path="/suporte/novo" element={<NovoTicket />} />
              <Route path="/entrar" element={<Login />} />
              <Route path="/cadastrar" element={<Register />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </NotificationsProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
