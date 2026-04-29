import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { ServiceCard } from '../components/ServiceCard';
import { FadeInSection } from '../components/FadeInSection';
import { Calendar } from 'lucide-react';
import { SocialButtons } from '../components/SocialButtons';

const completedServices = [
  {
    id: 'cs1',
    title: 'Limpeza Residencial',
    description: 'Serviço de limpeza completa',
    category: 'Limpeza',
    price: 150,
    rating: 4.8,
    reviewCount: 24,
    image:
      'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
    completedDate: '2024-03-15',
  },
  // Add more completed services
];

const recurringServices = [
  {
    id: 'rs1',
    title: 'Manutenção de Jardim',
    description: 'Manutenção mensal do jardim',
    category: 'Jardinagem',
    price: 200,
    rating: 5.0,
    reviewCount: 18,
    image:
      'https://images.unsplash.com/photo-1617575521317-d2974f3b56d2?auto=format&fit=crop&q=80',
    nextDate: '2024-03-30',
    frequency: 'Mensal',
  },
  // Add more recurring services
];

export function MyServicesPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('completed');
  const [contracts, setContracts] = useState<any[]>([]);

  React.useEffect(() => {
    fetch('http://127.0.0.1:8000/api/contratos/')
      .then((res) => res.json())
      .then((data) => {
        // Map DRF schema to frontend schema expected by ServiceCard
        const mapped = data.map((c: any) => ({
          id: c.id,
          title: c.titulo,
          description: c.descricao,
          category: c.categoria?.nome || 'Serviço',
          price: parseFloat(c.valor_acordado),
          rating: 5.0,
          reviewCount: 1,
          image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
          completedDate: c.data_conclusao || c.data_solicitacao,
        }));
        setContracts(mapped);
      })
      .catch((err) => console.error('Erro ao buscar contratos:', err));
  }, []);


  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <h1 className="text-3xl font-bold text-white mb-8">Meus Serviços</h1>

          <div className="flex space-x-4 mb-8">
            <button
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'completed'
                  ? 'bg-secondary text-black'
                  : 'bg-primary-light text-white hover:bg-primary'
              }`}
              onClick={() => setActiveTab('completed')}
            >
              Serviços Realizados
            </button>
            <button
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                activeTab === 'recurring'
                  ? 'bg-secondary text-black'
                  : 'bg-primary-light text-white hover:bg-primary'
              }`}
              onClick={() => setActiveTab('recurring')}
            >
              Serviços Recorrentes
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeTab === 'completed'
              ? contracts.map((service) => (
                  <div key={service.id} className="relative">
                    <div className="absolute top-4 right-4 bg-secondary text-black px-3 py-1 rounded-full font-semibold z-10">
                      Registrado em{' '}
                      {new Date(service.completedDate).toLocaleDateString()}
                    </div>
                    <ServiceCard service={service} />
                  </div>
                ))

              : recurringServices.map((service) => (
                  <div key={service.id} className="relative">
                    <div className="absolute top-4 right-4 bg-secondary text-black px-3 py-1 rounded-full font-semibold z-10 flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {new Date(service.nextDate).toLocaleDateString()}
                    </div>
                    <ServiceCard service={service} />
                    <div className="mt-2 text-center text-gray-400">
                      Frequência: {service.frequency}
                    </div>
                  </div>
                ))}
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
