import React from 'react';
import { Star, MapPin, Clock, Calendar } from 'lucide-react';
import { Professional } from '../../types';

interface ProfessionalInfoProps {
  professional: Professional;
}

export function ProfessionalInfo({ professional }: ProfessionalInfoProps) {
  return (
    <>
      <div className="flex items-center gap-2 mb-4">
        <Star className="h-6 w-6 text-secondary fill-current" />
        <span className="text-white text-lg font-semibold">{professional.rating}</span>
        <span className="text-gray-400">({professional.reviewCount} avaliações)</span>
      </div>

      <div className="space-y-4 text-gray-300">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-secondary" />
          <span>{professional.location}</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-secondary" />
          <span>{professional.experience} de experiência</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-secondary" />
          <span>Disponível: {professional.availability}</span>
        </div>
      </div>
    </>
  );
}