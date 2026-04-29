import React from 'react';
import { FadeInSection } from './FadeInSection';
import { Quote, Star } from 'lucide-react';

const testimonials = [
  {
    id: 1,
    name: "Maria Silva",
    role: "Cliente",
    content: "Encontrei um ótimo eletricista através do HIVEE. O serviço foi impecável e o preço justo. A plataforma facilitou todo o processo de contratação.",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80",
    rating: 5
  },
  {
    id: 2,
    name: "João Santos",
    role: "Prestador de Serviços",
    content: "Como prestador, o HIVEE me ajudou a expandir minha base de clientes e gerenciar meus serviços de forma eficiente. A plataforma é intuitiva e profissional.",
    image: "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&q=80",
    rating: 5
  },
  {
    id: 3,
    name: "Ana Costa",
    role: "Cliente",
    content: "A plataforma é intuitiva e encontrar profissionais qualificados nunca foi tão fácil. O sistema de avaliações me ajudou a escolher os melhores profissionais.",
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&q=80",
    rating: 5
  },
  {
    id: 4,
    name: "Pedro Oliveira",
    role: "Prestador de Serviços",
    content: "Desde que comecei a usar o HIVEE, minha agenda está sempre cheia. A plataforma me ajuda a gerenciar meus horários e clientes de forma profissional.",
    image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80",
    rating: 5
  }
];

export function Testimonials() {
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }).map((_, index) => (
      <Star
        key={index}
        className={`h-4 w-4 ${
          index < rating ? 'text-secondary fill-current' : 'text-gray-400'
        }`}
      />
    ));
  };

  return (
    <div className="relative py-32">
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection>
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full px-6 py-3 mb-8">
              <Quote className="h-5 w-5 text-secondary" />
              <span className="text-secondary font-medium">Depoimentos</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              O que dizem sobre nós
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Histórias reais de clientes e profissionais que fazem parte da nossa comunidade
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {testimonials.map((testimonial) => (
              <div
                key={testimonial.id}
                className="group bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:shadow-2xl hover:shadow-secondary/10 relative overflow-hidden"
              >
                <Quote className="absolute top-6 right-6 h-12 w-12 text-secondary/20" />
                <div className="flex items-center mb-6">
                  <img
                    src={testimonial.image}
                    alt={testimonial.name}
                    className="w-16 h-16 rounded-full object-cover mr-4 border-2 border-secondary/30"
                  />
                  <div>
                    <h3 className="text-white text-xl font-semibold">{testimonial.name}</h3>
                    <p className="text-gray-400">{testimonial.role}</p>
                    <div className="flex mt-2">
                      {renderStars(testimonial.rating)}
                    </div>
                  </div>
                </div>
                <p className="text-gray-300 text-lg italic leading-relaxed relative z-10">
                  "{testimonial.content}"
                </p>
              </div>
            ))}
          </div>
        </FadeInSection>
      </div>
    </div>
  );
}