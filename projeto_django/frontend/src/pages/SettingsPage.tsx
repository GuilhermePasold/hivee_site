import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { Bell, Lock, User, Globe, CreditCard } from 'lucide-react';
import { SocialButtons } from '../components/SocialButtons';

export function SettingsPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    sms: false,
  });

  const handleNotificationChange = (type: keyof typeof notifications) => {
    setNotifications((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <h1 className="text-3xl font-bold text-white mb-8">Configurações</h1>

          <div className="space-y-8">
            <div className="bg-primary-light p-6 rounded-lg">
              <div className="flex items-center mb-4">
                <Bell className="h-6 w-6 text-secondary mr-3" />
                <h2 className="text-xl font-semibold text-white">
                  Notificações
                </h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Notificações por Email</span>
                  <button
                    onClick={() => handleNotificationChange('email')}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notifications.email ? 'bg-secondary' : 'bg-gray-600'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform transform ${
                        notifications.email ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Notificações Push</span>
                  <button
                    onClick={() => handleNotificationChange('push')}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notifications.push ? 'bg-secondary' : 'bg-gray-600'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform transform ${
                        notifications.push ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Notificações SMS</span>
                  <button
                    onClick={() => handleNotificationChange('sms')}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notifications.sms ? 'bg-secondary' : 'bg-gray-600'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform transform ${
                        notifications.sms ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-primary-light p-6 rounded-lg">
              <div className="flex items-center mb-4">
                <Lock className="h-6 w-6 text-secondary mr-3" />
                <h2 className="text-xl font-semibold text-white">Segurança</h2>
              </div>
              <div className="space-y-4">
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Alterar Senha
                </button>
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Autenticação em Duas Etapas
                </button>
              </div>
            </div>

            <div className="bg-primary-light p-6 rounded-lg">
              <div className="flex items-center mb-4">
                <CreditCard className="h-6 w-6 text-secondary mr-3" />
                <h2 className="text-xl font-semibold text-white">Pagamento</h2>
              </div>
              <div className="space-y-4">
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Gerenciar Métodos de Pagamento
                </button>
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Histórico de Transações
                </button>
              </div>
            </div>

            <div className="bg-primary-light p-6 rounded-lg">
              <div className="flex items-center mb-4">
                <Globe className="h-6 w-6 text-secondary mr-3" />
                <h2 className="text-xl font-semibold text-white">
                  Preferências
                </h2>
              </div>
              <div className="space-y-4">
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Idioma
                </button>
                <button className="w-full text-left text-gray-300 hover:text-white transition-colors">
                  Fuso Horário
                </button>
              </div>
            </div>
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
