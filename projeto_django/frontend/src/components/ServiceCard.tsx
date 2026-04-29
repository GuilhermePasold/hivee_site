import React from 'react';
import { Star } from 'lucide-react';
import { Service } from '../types';
import { useNavigate } from 'react-router-dom';

interface ServiceCardProps {
  service: Service;
}

export function ServiceCard({ service }: ServiceCardProps) {
  const navigate = useNavigate();

  const renderStars = (rating: number) => {
    return [...Array(5)].map((_, index) => (
      <Star
        key={index}
        className={`h-5 w-5 ${
          index < rating ? 'text-secondary fill-current' : 'text-gray-400'
        }`}
      />
    ));
  };

  const handleHire = () => {
    navigate(`/professional/${service.id}`);
  };

  return (
    <div className="bg-primary rounded-lg overflow-hidden shadow-lg transform transition-all duration-300 hover:scale-105">
      <div className="relative pb-[56.25%]">
        <img
          src={service.image}
          alt={service.title}
          className="absolute top-0 left-0 w-full h-full object-cover"
          loading="lazy"
        />
      </div>
      <div className="p-4">
        <h3 className="text-white font-semibold text-lg mb-2">{service.title}</h3>
        <p className="text-gray-400 text-sm mb-3">{service.description}</p>
        <div className="flex items-center mb-3">
          {renderStars(service.rating)}
          <span className="ml-2 text-gray-400 text-sm">({service.reviewCount})</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-secondary font-bold">
            R$ {service.price.toFixed(2)}/hora
          </span>
          <button 
            onClick={handleHire}
            className="bg-secondary text-black px-4 py-2 rounded-lg font-semibold hover:bg-secondary-light transition-colors"
          >
            Contratar
          </button>
        </div>
      </div>
    </div>
  );
}