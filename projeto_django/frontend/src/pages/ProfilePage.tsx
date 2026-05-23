import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { Camera, Mail, Phone, MapPin, Star, Trophy, LogOut, Trash2 } from 'lucide-react';
import { BenefitsSection } from '../components/achievements/BenefitsSection';
import { SocialButtons } from '../components/SocialButtons';

interface ProfileData {
  first_name: string;
  last_name: string;
  email: string;
  cidade: string;
  estado: string;
  telefone: string;
  cep: string;
}

export function ProfilePage() {
  const navigate = useNavigate();
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [profile, setProfile] = useState<ProfileData>({
    first_name: '',
    last_name: '',
    email: '',
    cidade: '',
    estado: '',
    telefone: '',
    cep: '',
  });

  const token = localStorage.getItem('user_token') || '';

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    fetch('http://127.0.0.1:8000/api/profile/', {
      headers: {
        Authorization: `Token ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Não foi possível carregar o perfil');
        }
        return res.json();
      })
      .then((data) => {
        if (!data.success) {
          throw new Error(data.message || 'Perfil não encontrado');
        }

        const profileData = data.profile;
        setProfile({
          first_name: profileData.first_name || '',
          last_name: profileData.last_name || '',
          email: profileData.email || '',
          cidade: profileData.cidade || '',
          estado: profileData.estado || '',
          telefone: profileData.telefone || '',
          cep: profileData.cep || '',
        });

        localStorage.setItem('user_data', JSON.stringify(profileData));
      })
      .catch((err) => {
        console.error('Erro ao carregar perfil:', err);
        setError('Não foi possível carregar os dados do perfil.');
      })
      .finally(() => setIsLoading(false));
  }, [navigate, token]);

  const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(' ') || 'Usuário Conectado';
  const address = [profile.cidade, profile.estado].filter(Boolean).join(', ') || 'Localização não informada';

  const handleFieldChange = (field: keyof ProfileData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { value } = e.target;
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    setIsSaving(true);
    setError('');
    setSuccessMessage('');

    fetch('http://127.0.0.1:8000/api/profile/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Token ${token}`,
      },
      body: JSON.stringify(profile),
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          throw new Error(data.message || 'Falha ao atualizar perfil');
        }

        setSuccessMessage(data.message || 'Perfil atualizado com sucesso');
        localStorage.setItem('user_data', JSON.stringify(profile));
        setIsEditing(false);
      })
      .catch((err) => {
        console.error('Erro ao salvar perfil:', err);
        setError('Não foi possível salvar as alterações.');
      })
      .finally(() => setIsSaving(false));
  };

  const handleLogout = () => {
    fetch('http://127.0.0.1:8000/api/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Token ${token}`,
      },
      body: JSON.stringify({ token }),
    }).finally(() => {
      localStorage.removeItem('user_token');
      localStorage.removeItem('user_data');
      navigate('/login');
    });
  };

  const handleDelete = () => {
    if (!window.confirm('Tem certeza que deseja excluir sua conta?')) {
      return;
    }

    setIsDeleting(true);
    setError('');

    fetch('http://127.0.0.1:8000/api/profile/', {
      method: 'DELETE',
      headers: {
        Authorization: `Token ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          throw new Error(data.message || 'Falha ao excluir a conta');
        }

        localStorage.removeItem('user_token');
        localStorage.removeItem('user_data');
        navigate('/login');
      })
      .catch((err) => {
        console.error('Erro ao excluir conta:', err);
        setError('Não foi possível excluir sua conta.');
      })
      .finally(() => setIsDeleting(false));
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
            {error && (
              <div className="mb-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg p-3 text-sm text-center">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="mb-4 bg-green-500/10 border border-green-500/30 text-green-500 rounded-lg p-3 text-sm text-center">
                {successMessage}
              </div>
            )}
            {isLoading ? (
              <p className="text-gray-300">Carregando perfil...</p>
            ) : (
              <>
            <div className="flex flex-col md:flex-row items-start gap-8">
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80"
                  alt={fullName}
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
                      {fullName}
                    </h1>
                    <div className="flex items-center gap-2 text-gray-400 mb-4">
                      <Star className="h-5 w-5 text-secondary fill-current" />
                      <span>5.0</span>
                      <span>(12 avaliações)</span>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-wrap justify-end">
                    <button
                      onClick={() => (isEditing ? handleSave() : setIsEditing(true))}
                      className="px-4 py-2 bg-secondary text-black rounded-lg hover:bg-secondary-light transition-colors"
                      disabled={isSaving}
                    >
                      {isSaving ? 'Salvando...' : isEditing ? 'Salvar' : 'Editar Perfil'}
                    </button>
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors inline-flex items-center gap-2"
                    >
                      <LogOut className="h-4 w-4" />
                      Sair
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-gray-300">
                    <Mail className="h-5 w-5 text-secondary" />
                    <span>{profile.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-300">
                    <Phone className="h-5 w-5 text-secondary" />
                    {isEditing ? (
                      <input
                        value={profile.telefone}
                        onChange={handleFieldChange('telefone')}
                        className="w-full max-w-xs px-3 py-2 bg-primary border border-gray-700 rounded-lg text-white"
                      />
                    ) : (
                      <span>{profile.telefone || 'Telefone não informado'}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-gray-300">
                    <MapPin className="h-5 w-5 text-secondary" />
                    {isEditing ? (
                      <div className="flex gap-2 flex-wrap">
                        <input
                          value={profile.cidade}
                          onChange={handleFieldChange('cidade')}
                          placeholder="Cidade"
                          className="w-full max-w-xs px-3 py-2 bg-primary border border-gray-700 rounded-lg text-white"
                        />
                        <input
                          value={profile.estado}
                          onChange={handleFieldChange('estado')}
                          placeholder="UF"
                          className="w-20 px-3 py-2 bg-primary border border-gray-700 rounded-lg text-white uppercase"
                          maxLength={2}
                        />
                        <input
                          value={profile.cep}
                          onChange={handleFieldChange('cep')}
                          placeholder="CEP"
                          className="w-full max-w-[140px] px-3 py-2 bg-primary border border-gray-700 rounded-lg text-white"
                        />
                      </div>
                    ) : (
                      <span>{address} {profile.cep ? `- CEP ${profile.cep}` : ''}</span>
                    )}
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
                    150 / 500 XP para o próximo nível
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
                  <p className="text-gray-300">
                    {isEditing
                      ? 'Use os campos acima para atualizar seu perfil, incluindo CEP.'
                      : 'Profissional parceiro ou cliente do ecossistema.'}
                  </p>
                  <div className="mt-6 flex gap-3 flex-wrap">
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors inline-flex items-center gap-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      {isDeleting ? 'Excluindo...' : 'Excluir conta'}
                    </button>
                  </div>
                </div>
              ) : (
                <BenefitsSection />
              )}
            </div>
              </>
            )}
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
