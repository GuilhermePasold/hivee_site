import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { Camera, Mail, Phone, MapPin, Star, Trophy } from 'lucide-react';
import { BenefitsSection } from '../components/achievements/BenefitsSection';
import { SocialButtons } from '../components/SocialButtons';

export function ProfilePage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');

  // Load from session
  const storedUser = JSON.parse(localStorage.getItem('user_data') || '{}');

  const profile = {
    name: storedUser.first_name ? `${storedUser.first_name} ${storedUser.last_name}` : 'Usuário Conectado',
    email: storedUser.email || 'usuario@email.com',
    phone: '(11) 99999-9999',
    address: 'Caçador, SC',

    rating: 5.0,
    reviewCount: 12,
    bio: 'Profissional parceiro ou cliente do ecossistema.',
    image:
      'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80',
    level: 1,
    xp: 150,
    nextLevelXp: 500,
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
          <div className="bg-primary-light rounded-lg p-8">
            <div className="flex flex-col md:flex-row items-start gap-8">
              <div className="relative">
                <img
                  src={profile.image}
                  alt={profile.name}
                  className="w-32 h-32 rounded-full object-cover border-4 border-secondary"
                />
                <button className="absolute bottom-0 right-0 p-2 bg-secondary rounded-full hover:bg-secondary-light transition-colors">
                  <Camera className="h-5 w-5 text-black" />
                </button>
                <div className="absolute -top-2 -right-2 bg-secondary text-black px-2 py-1 rounded-full text-sm font-bold">
                  Nível {profile.level}
                </div>
              </div>

              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                      {profile.name}
                    </h1>
                    <div className="flex items-center gap-2 text-gray-400 mb-4">
                      <Star className="h-5 w-5 text-secondary fill-current" />
                      <span>{profile.rating}</span>
                      <span>({profile.reviewCount} avaliações)</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="px-4 py-2 bg-secondary text-black rounded-lg hover:bg-secondary-light transition-colors"
                  >
                    {isEditing ? 'Salvar' : 'Editar Perfil'}
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-gray-300">
                    <Mail className="h-5 w-5 text-secondary" />
                    <span>{profile.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-300">
                    <Phone className="h-5 w-5 text-secondary" />
                    <span>{profile.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-300">
                    <MapPin className="h-5 w-5 text-secondary" />
                    <span>{profile.address}</span>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Trophy className="h-5 w-5 text-secondary" />
                    <span className="text-white font-semibold">
                      Progresso do Nível
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                    <div
                      className="bg-secondary rounded-full h-2 transition-all duration-300"
                      style={{
                        width: `${(profile.xp / profile.nextLevelXp) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="text-gray-400 text-sm">
                    {profile.xp} / {profile.nextLevelXp} XP para o próximo nível
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8">
              <div className="border-b border-gray-700 mb-6">
                <button
                  className={`px-6 py-3 font-semibold transition-colors ${
                    activeTab === 'profile'
                      ? 'text-secondary border-b-2 border-secondary'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  onClick={() => setActiveTab('profile')}
                >
                  Perfil
                </button>
                <button
                  className={`px-6 py-3 font-semibold transition-colors ${
                    activeTab === 'benefits'
                      ? 'text-secondary border-b-2 border-secondary'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  onClick={() => setActiveTab('benefits')}
                >
                  Meus Benefícios
                </button>
              </div>

              {activeTab === 'profile' ? (
                <div className="mt-6">
                  <h2 className="text-xl font-semibold text-white mb-2">
                    Sobre
                  </h2>
                  <p className="text-gray-300">{profile.bio}</p>
                </div>
              ) : (
                <BenefitsSection />
              )}
            </div>
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
