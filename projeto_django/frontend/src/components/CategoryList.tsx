import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { iconMap } from '../utils/iconMap';
import { useLocationStore } from '../stores/locationStore';

interface Category {
  id: string;
  nome: string;
  slug: string;
  icone: string;
}

export function CategoryList() {
  const navigate = useNavigate();
  const [categoriesList, setCategoriesList] = useState<Category[]>([]);
  const { selectedLocation } = useLocationStore();

  useEffect(() => {
    if (!selectedLocation) {
      setCategoriesList([]);
      return;
    }

    // Fetch providers for this location to see which categories exist
    const url = `http://127.0.0.1:8000/api/prestadores/?localizacao=${encodeURIComponent(selectedLocation.display_name)}`;
    
    fetch(url)
      .then(res => res.json())
      .then(data => {
        const uniqueCategoriesMap: Record<string, Category> = {};
        
        data.forEach((p: any) => {
          if (p.especialidades && Array.isArray(p.especialidades)) {
            p.especialidades.forEach((cat: any) => {
              uniqueCategoriesMap[cat.id.toString()] = {
                id: cat.id.toString(),
                nome: cat.nome,
                slug: cat.slug,
                icone: cat.icone
              };
            });
          }
        });
        
        setCategoriesList(Object.values(uniqueCategoriesMap));
      })
      .catch(err => console.error('Error fetching dynamic categories:', err));
  }, [selectedLocation]);

  if (!selectedLocation) {
    return (
      <div className="col-span-full text-center py-12 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md">
        <p className="text-xl text-gray-400">
          Selecione uma localização para visualizar as categorias de serviços disponíveis.
        </p>
      </div>
    );
  }

  if (categoriesList.length === 0) {
    return (
      <div className="col-span-full text-center py-12 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md">
        <p className="text-xl text-gray-400">
          Nenhuma categoria de serviço disponível para a região selecionada no momento.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {categoriesList.map((category) => {
        let Icon = iconMap.MoreHorizontal;
        if (category.icone === '⚡') Icon = iconMap.Zap;
        if (category.icone === '🔧') Icon = iconMap.Wrench;
        if (category.icone === '🧹') Icon = iconMap.Sparkles;
        if (category.icone === '🎨') Icon = iconMap.Palette;
        if (category.icone === '🌿') Icon = iconMap.Flower2;

        return (
          <button
            key={category.id}
            className="group flex flex-col items-center p-8 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:shadow-2xl hover:shadow-secondary/10 hover:-translate-y-2"
            onClick={() => navigate(`/category/${category.id}`)}
          >
            <div className="bg-secondary/10 p-4 rounded-2xl mb-4 group-hover:bg-secondary/20 transition-colors">
              {Icon && <Icon className="h-8 w-8 text-secondary" />}
            </div>
            <span className="text-white text-lg font-medium group-hover:text-secondary transition-colors">
              {category.nome}
            </span>
          </button>
        );
      })}
    </div>
  );
}