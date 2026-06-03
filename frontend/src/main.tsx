import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import "./index.css";
import { AuthProvider } from "@/context/AuthContext";
import Layout from "@/components/Layout";
import Home from "@/pages/Home";
import Search from "@/pages/Search";
import Recommended from "@/pages/Recommended";
import ProviderProfile from "@/pages/ProviderProfile";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import BecomeProvider from "@/pages/BecomeProvider";
import MinhaConta from "@/pages/MinhaConta";

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
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/buscar" element={<Search />} />
            <Route path="/recomendados" element={<Recommended />} />
            <Route path="/prestador/:slug" element={<ProviderProfile />} />
            <Route path="/sou-prestador" element={<BecomeProvider />} />
            <Route path="/minha-conta" element={<MinhaConta />} />
            <Route path="/entrar" element={<Login />} />
            <Route path="/cadastrar" element={<Register />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
