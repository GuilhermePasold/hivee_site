import React from 'react';
import { SearchLocation } from './SearchLocation';

export function Hero() {
  return (
    <div className="relative min-h-screen flex items-center justify-center">

      <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32 w-full">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full px-6 py-3 mb-8">
            <div className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
            <span className="text-secondary font-medium text-sm">Profissionais pertinho de você</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-8 leading-tight">
            <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              Encontre profissionais para
            </span>
            <br />
            <span className="bg-gradient-to-r from-secondary via-yellow-400 to-secondary bg-clip-text text-transparent">
              qualquer serviço
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Conectamos você aos melhores profissionais da sua região com segurança, qualidade e rapidez
          </p>
          
          <SearchLocation className="max-w-2xl mx-auto" />
          
          <div className="flex items-center justify-center gap-8 mt-12 text-gray-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full" />
              <span className="text-sm">Verificação completa</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full" />
              <span className="text-sm">Pagamento seguro</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full" />
              <span className="text-sm">Suporte 24/7</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}