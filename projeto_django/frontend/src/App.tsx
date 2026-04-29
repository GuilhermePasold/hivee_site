import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { CategoryPage } from './pages/CategoryPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PostDemandPage } from './pages/PostDemandPage';
import { MyServicesPage } from './pages/MyServicesPage';
import { ProfilePage } from './pages/ProfilePage';
import { BecomeProfessionalPage } from './pages/BecomeProfessionalPage';
import { SupportPage } from './pages/SupportPage';
import { HelpPage } from './pages/HelpPage';
import { SettingsPage } from './pages/SettingsPage';
import { ServiceMatchPage } from './pages/ServiceMatchPage';
import { ProfessionalProfilePage } from './pages/ProfessionalProfilePage';
import { SocialButtons } from './components/SocialButtons';

function App() {
  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/category/:id" element={<CategoryPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/post-demand" element={<PostDemandPage />} />
          <Route path="/my-services" element={<MyServicesPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="/become-professional"
            element={<BecomeProfessionalPage />}
          />
          <Route path="/support" element={<SupportPage />} />
          <Route path="/help" element={<HelpPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/service-match" element={<ServiceMatchPage />} />
          <Route
            path="/professional/:id"
            element={<ProfessionalProfilePage />}
          />
          <Route path="/services" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Página de Serviços em Desenvolvimento</h1></div>} />
          <Route path="/how-it-works" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Como Funciona - Em Desenvolvimento</h1></div>} />
          <Route path="/about" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Sobre Nós - Em Desenvolvimento</h1></div>} />
          <Route path="/careers" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Carreiras - Em Desenvolvimento</h1></div>} />
          <Route path="/contact" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Contato - Em Desenvolvimento</h1></div>} />
          <Route path="/status" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Status do Sistema - Em Desenvolvimento</h1></div>} />
          <Route path="/terms" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Termos de Uso - Em Desenvolvimento</h1></div>} />
          <Route path="/privacy" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Política de Privacidade - Em Desenvolvimento</h1></div>} />
          <Route path="/cookies" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Política de Cookies - Em Desenvolvimento</h1></div>} />
          <Route path="/security" element={<div className="min-h-screen bg-black flex items-center justify-center"><h1 className="text-white text-2xl">Segurança - Em Desenvolvimento</h1></div>} />
        </Routes>
      </Router>
      <SocialButtons />
    </>
  );
}

export default App;
