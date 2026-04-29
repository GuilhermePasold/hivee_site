import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Professional } from '../types';

export function useProfessionalData(): Professional {
  const { id } = useParams<{ id: string }>();
  const [professional, setProfessional] = useState<Professional>({
    id: id || '0',
    name: 'Carregando...',
    title: 'Aguarde',
    rating: 5.0,
    reviewCount: 0,
    location: 'Buscando...',
    experience: '...',
    price: 0,
    availability: 'Consulta pendente',
    image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
    certifications: [],
    reviews: [],
  });

  useEffect(() => {
    if (!id) return;
    fetch(`http://127.0.0.1:8000/api/prestadores/${id}/`)
      .then((res) => res.json())
      .then((p: any) => {
        let locationStr = '';
        if (p.cidade && p.estado) {
          locationStr = `${p.cidade}/${p.estado}`;
        } else if (p.cidade || p.estado) {
          locationStr = p.cidade || p.estado;
        }

        setProfessional({
          id: p.id.toString(),
          name: `${p.user.first_name || ''} ${p.user.last_name || ''}`,
          title: p.especialidades[0]?.nome || 'Prestador de Serviços',
          rating: parseFloat(p.nota_media) || 5.0,
          reviewCount: p.total_servicos || 0,
          location: locationStr || 'Não informada',
          experience: `${p.anos_experiencia || 0} anos`,
          price: parseFloat(p.valor_hora),
          availability: p.disponivel ? 'Disponível' : 'Indisponível',
          image: p.foto || 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&q=80',
          certifications: [],
          reviews: [],
        });
      })
      .catch((err) => console.error('Erro ao buscar dados do prestador:', err));
  }, [id]);

  return professional;
}