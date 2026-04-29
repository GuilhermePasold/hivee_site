import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Play, Pause } from 'lucide-react';
import { ModernServiceCard } from './ModernServiceCard';
import { useLocationStore } from '../stores/locationStore';

interface Service {
  id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  rating: number;
  reviewCount: number;
  image: string;
  location?: string;
}

export function ProfessionalCarousel() {
  const [services, setServices] = useState<Service[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const { selectedLocation, searchQuery } = useLocationStore();

  useEffect(() => {
    let url = 'http://127.0.0.1:8000/api/prestadores/?';
    if (selectedLocation) {
      url += `localizacao=${encodeURIComponent(selectedLocation.display_name)}&`;
    }
    if (searchQuery) {
      url += `search=${encodeURIComponent(searchQuery)}&`;
    }

    fetch(url)
      .then(res => res.json())
      .then(data => {
        const mapped = data.map((p: any) => {
          let locationStr = '';
          if (p.cidade && p.estado) {
            locationStr = `${p.cidade}/${p.estado}`;
          } else if (p.cidade || p.estado) {
            locationStr = p.cidade || p.estado;
          }
          
          return {
            id: p.id.toString(),
            title: `${p.user.first_name || ''} ${p.user.last_name || ''} - ${p.especialidades[0]?.nome || 'Geral'}`,
            description: p.bio,
            category: p.especialidades[0]?.nome || 'Serviços',
            price: parseFloat(p.valor_hora),
            rating: parseFloat(p.nota_media) || 5.0,
            reviewCount: p.total_servicos || 0,
            image: p.foto || 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
            location: locationStr
          };
        });
        setServices(mapped);
      })
      .catch(err => console.error('Error fetching providers:', err));
  }, [selectedLocation, searchQuery]);


  const itemsPerPage = window.innerWidth >= 1024 ? 3 : window.innerWidth >= 768 ? 2 : 1;
  const totalPages = Math.ceil(services.length / itemsPerPage) || 1;

  // Auto-play functionality
  useEffect(() => {
    if (!isAutoPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % totalPages);
    }, 4000);

    return () => clearInterval(interval);
  }, [isAutoPlaying, totalPages]);

  const nextSlide = () => {
    setIsLoading(true);
    setCurrentIndex((prev) => (prev + 1) % totalPages);
    setTimeout(() => setIsLoading(false), 300);
  };

  const prevSlide = () => {
    setIsLoading(true);
    setCurrentIndex((prev) => (prev - 1 + totalPages) % totalPages);
    setTimeout(() => setIsLoading(false), 300);
  };

  const goToSlide = (index: number) => {
    setIsLoading(true);
    setCurrentIndex(index);
    setTimeout(() => setIsLoading(false), 300);
  };

  const visibleServices = services.slice(
    currentIndex * itemsPerPage,
    (currentIndex + 1) * itemsPerPage
  );

  return (
    <div className="relative group">
      {/* Carousel Controls */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full hover:bg-white/10 transition-all duration-300 text-white"
          >
            {isAutoPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span className="text-sm">{isAutoPlaying ? 'Pausar' : 'Reproduzir'}</span>
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={prevSlide}
            disabled={isLoading}
            className="p-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full hover:bg-white/10 hover:border-secondary/30 transition-all duration-300 disabled:opacity-50 group"
          >
            <ChevronLeft className="h-5 w-5 text-white group-hover:text-secondary transition-colors" />
          </button>
          
          <button
            onClick={nextSlide}
            disabled={isLoading}
            className="p-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full hover:bg-white/10 hover:border-secondary/30 transition-all duration-300 disabled:opacity-50 group"
          >
            <ChevronRight className="h-5 w-5 text-white group-hover:text-secondary transition-colors" />
          </button>
        </div>
      </div>

      {/* Carousel Content */}
      <div className="relative overflow-hidden rounded-2xl">
        <div 
          className="flex transition-transform duration-500 ease-out"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {Array.from({ length: totalPages }).map((_, pageIndex) => (
            <div key={pageIndex} className="w-full flex-shrink-0">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 px-2">
                {services
                  .slice(pageIndex * itemsPerPage, (pageIndex + 1) * itemsPerPage)
                  .map((service) => (
                    <div 
                      key={service.id}
                      className={`transform transition-all duration-300 ${
                        isLoading ? 'opacity-50 scale-95' : 'opacity-100 scale-100'
                      }`}
                    >
                      <ModernServiceCard service={service} />
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-8 flex items-center justify-center gap-4">
        <div className="flex gap-2">
          {Array.from({ length: totalPages }).map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`h-2 rounded-full transition-all duration-300 ${
                index === currentIndex 
                  ? 'w-8 bg-secondary' 
                  : 'w-2 bg-white/30 hover:bg-white/50'
              }`}
            />
          ))}
        </div>
        
        <div className="text-sm text-gray-400 ml-4">
          {currentIndex + 1} de {totalPages}
        </div>
      </div>
    </div>
  );
}