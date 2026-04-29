import React from 'react';
import { Star, MapPin, Clock, Award, Heart } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { ImageSwiper } from './ui/image-swiper';
import { Button } from './ui/button';
import { useNavigate } from 'react-router-dom';

interface ModernServiceCardProps {
  service: {
    id: string;
    title: string;
    description: string;
    category: string;
    price: number;
    rating: number;
    reviewCount: number;
    image: string;
    matchScore?: number;
    location?: string;
    availability?: string;
  };
}

export function ModernServiceCard({ service }: ModernServiceCardProps) {
  const navigate = useNavigate();
  
  // Create multiple images for the swiper
  const images = [
    service.image,
    service.image.replace('?auto=format&fit=crop&q=80', '?auto=format&fit=crop&q=80&w=800'),
    service.image.replace('?auto=format&fit=crop&q=80', '?auto=format&fit=crop&q=80&h=600'),
  ];

  const handleHire = () => {
    navigate(`/professional/${service.id}`);
  };

  return (
    <Card className="group overflow-hidden bg-white/5 backdrop-blur-xl border border-white/10 hover:border-secondary/30 transition-all duration-500 hover:shadow-2xl hover:shadow-secondary/10 hover:-translate-y-2">
      <CardContent className="p-0">
        <div className="relative">
          <ImageSwiper images={images} className="aspect-[4/3]" />
          {service.matchScore && (
            <div className="absolute top-4 right-4 bg-secondary text-black px-3 py-1.5 rounded-full text-sm font-bold shadow-lg backdrop-blur-sm">
              {service.matchScore}% Match
            </div>
          )}
          <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm text-white px-3 py-1.5 rounded-full text-xs font-medium border border-white/20">
            {service.category}
          </div>
          <button className="absolute top-4 right-16 bg-black/60 backdrop-blur-sm text-white p-2 rounded-full hover:bg-black/80 transition-colors border border-white/20">
            <Heart className="h-4 w-4" />
          </button>
        </div>
      </CardContent>
      
      <div className="p-6 space-y-4">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-white group-hover:text-secondary transition-colors line-clamp-2 leading-tight">
            {service.title}
          </h3>
          <div className="flex items-center gap-1 ml-2 bg-white/10 px-2 py-1 rounded-full">
            <Star className="h-3 w-3 text-secondary fill-current" />
            <span className="text-sm font-medium text-white">{service.rating}</span>
          </div>
        </div>
        
        <p className="text-gray-400 text-sm line-clamp-2 leading-relaxed">
          {service.description}
        </p>
        
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {service.location && (
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              <span>{service.location}</span>
            </div>
          )}
          {service.availability && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{service.availability}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Award className="h-3 w-3" />
            <span>{service.reviewCount} avaliações</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between pt-2 border-t border-white/10">
          <div className="flex flex-col">
            <span className="text-2xl font-bold text-secondary">
              R$ {service.price}
            </span>
            <span className="text-xs text-gray-500">por hora</span>
          </div>
          
          <Button 
            onClick={handleHire}
            className="bg-secondary hover:bg-secondary/90 text-black font-semibold px-6 py-2.5 rounded-xl transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-secondary/25"
          >
            Contratar
          </Button>
        </div>
      </div>
    </Card>
  );
}