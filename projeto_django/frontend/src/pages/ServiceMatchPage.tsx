import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { ModernServiceCard } from '../components/ModernServiceCard';
import { Sparkles, Target, ThumbsUp, Clock, Zap } from 'lucide-react';
import { SocialButtons } from '../components/SocialButtons';

const matchedServices = [
  {
    id: 'ms1',
    title: 'Ana Silva - Limpeza',
    description: 'Especialista em limpeza residencial com 5 anos de experiência',
    category: 'Limpeza',
    price: 160,
    rating: 4.8,
    reviewCount: 156,
    image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
    matchScore: 95,
    location: 'Caçador, SC',

    availability: 'Seg-Sáb'
  },
  {
    id: 'ms2',
    title: 'Carlos Santos - Montador',
    description: 'Montador profissional certificado com garantia de serviço',
    category: 'Montagem',
    price: 120,
    rating: 4.9,
    reviewCount: 203,
    image: 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?auto=format&fit=crop&q=80',
    matchScore: 92,
    location: 'Rio de Janeiro, RJ',
    availability: 'Seg-Dom'
  },
  {
    id: 'ms3',
    title: 'Marina Lima - Jardinagem',
    description: 'Paisagista especializada em jardins modernos e sustentáveis',
    category: 'Jardinagem',
    price: 180,
    rating: 4.7,
    reviewCount: 89,
    image: 'https://images.unsplash.com/photo-1617575521317-d2974f3b56d2?auto=format&fit=crop&q=80',
    matchScore: 88,
    location: 'Curitiba, PR',
    availability: 'Ter-Sáb'
  }
];

export function ServiceMatchPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu isOpen={isSideMenuOpen} onClose={() => setIsSideMenuOpen(false)} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-3 bg-secondary/10 backdrop-blur-sm border border-secondary/20 rounded-full px-6 py-3 mb-6">
              <Sparkles className="h-6 w-6 text-secondary" />
              <span className="text-secondary font-semibold">Match Inteligente</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              Seus Matches Perfeitos
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Nossa IA analisou suas preferências e encontrou os profissionais ideais para você
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300">
              <div className="flex items-center gap-4 mb-4">
                <div className="bg-secondary/10 p-3 rounded-xl group-hover:bg-secondary/20 transition-colors">
                  <Target className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-white">Preferências</h3>
              </div>
              <p className="text-gray-400 leading-relaxed">
                Analisamos seu histórico e preferências para encontrar profissionais ideais
              </p>
            </div>

            <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300">
              <div className="flex items-center gap-4 mb-4">
                <div className="bg-secondary/10 p-3 rounded-xl group-hover:bg-secondary/20 transition-colors">
                  <ThumbsUp className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-white">Avaliações</h3>
              </div>
              <p className="text-gray-400 leading-relaxed">
                Profissionais altamente avaliados por clientes com perfis similares
              </p>
            </div>

            <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300">
              <div className="flex items-center gap-4 mb-4">
                <div className="bg-secondary/10 p-3 rounded-xl group-hover:bg-secondary/20 transition-colors">
                  <Clock className="h-6 w-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-white">Disponibilidade</h3>
              </div>
              <p className="text-gray-400 leading-relaxed">
                Horários compatíveis com sua agenda e necessidades
              </p>
            </div>
          </div>

          <div className="bg-zinc-900/20 backdrop-blur-sm border border-zinc-800 p-6 rounded-2xl mb-12">
            <div className="flex items-center gap-4">
              <div className="bg-secondary/10 p-3 rounded-xl">
                <Zap className="h-6 w-6 text-secondary" />
              </div>
              <p className="text-gray-300 text-lg">
                Nossa tecnologia analisa mais de <span className="text-secondary font-semibold">20 fatores</span> para garantir o match perfeito entre você e o profissional
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {matchedServices.map(service => (
              <ModernServiceCard key={service.id} service={service} />
            ))}
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}