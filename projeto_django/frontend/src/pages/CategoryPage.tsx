import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { ServiceCard } from '../components/ServiceCard';
import { FadeInSection } from '../components/FadeInSection';
import { SocialButtons } from '../components/SocialButtons';

interface Category {
  id: number;
  nome: string;
  slug: string;
}

interface Service {
  id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  rating: number;
  reviewCount: number;
  image: string;
}

export function CategoryPage() {
  const { id } = useParams();
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [category, setCategory] = useState<Category | null>(null);
  const [services, setServices] = useState<Service[]>([]);

  useEffect(() => {
    // Fetch categories to find the current one
    fetch('http://127.0.0.1:8000/api/categorias/')
      .then(res => res.json())
      .then((data: Category[]) => {
        const found = data.find(c => c.id.toString() === id);
        if (found) setCategory(found);
      })
      .catch(err => console.error('Error fetching categories:', err));

    // Fetch providers filtered by category ID
    fetch(`http://127.0.0.1:8000/api/prestadores/?categoria=${id}`)
      .then(res => res.json())
      .then(data => {
        const mapped = data.map((p: any) => ({
          id: p.id.toString(),
          title: `${p.user.first_name || ''} ${p.user.last_name || ''}`,
          description: p.bio,
          category: p.especialidades[0]?.nome || 'Geral',
          price: parseFloat(p.valor_hora),
          rating: parseFloat(p.nota_media) || 5.0,
          reviewCount: p.total_servicos || 0,
          image: p.foto || 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
        }));
        setServices(mapped);
      })
      .catch(err => console.error('Error fetching services for category:', err));
  }, [id]);

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <h1 className="text-3xl font-bold text-white mb-8">
            {category?.nome || 'Serviços'}
          </h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => (
              <ServiceCard key={service.id} service={service} />
            ))}
          </div>
          {services.length === 0 && (
            <p className="text-gray-400 text-center py-12 text-lg">
              Nenhum profissional cadastrado para esta categoria ainda.
            </p>
          )}
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}

