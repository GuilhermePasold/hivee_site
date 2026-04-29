import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { MessageSquare, Phone, Mail } from 'lucide-react';
import { SocialButtons } from '../components/SocialButtons';

export function SupportPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [subject, setSubject] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle support message submission
  };

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <h1 className="text-3xl font-bold text-white mb-8">Suporte</h1>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <div className="bg-primary-light p-6 rounded-lg text-center">
              <MessageSquare className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">
                Chat Online
              </h2>
              <p className="text-gray-400">Disponível 24/7 para ajudar você</p>
            </div>

            <div className="bg-primary-light p-6 rounded-lg text-center">
              <Phone className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">
                Telefone
              </h2>
              <p className="text-gray-400">0800 123 4567</p>
            </div>

            <div className="bg-primary-light p-6 rounded-lg text-center">
              <Mail className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Email</h2>
              <p className="text-gray-400">suporte@hivee.com</p>
            </div>
          </div>

          <div className="bg-primary-light p-8 rounded-lg">
            <h2 className="text-2xl font-bold text-white mb-6">
              Envie sua Mensagem
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="subject"
                  className="block text-sm font-medium text-white mb-2"
                >
                  Assunto
                </label>
                <input
                  type="text"
                  id="subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-2 bg-primary border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="message"
                  className="block text-sm font-medium text-white mb-2"
                >
                  Mensagem
                </label>
                <textarea
                  id="message"
                  rows={6}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full px-4 py-2 bg-primary border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                  required
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="px-6 py-3 bg-secondary text-black rounded-lg hover:bg-secondary-light transition-colors font-semibold"
                >
                  Enviar Mensagem
                </button>
              </div>
            </form>
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
