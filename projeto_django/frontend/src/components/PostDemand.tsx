import React from 'react';
import { ArrowRight, Search, Clock, CheckCircle, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function PostDemand() {
  const navigate = useNavigate();

  return (
    <>
    <div className="relative py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-secondary/10 backdrop-blur-sm border border-secondary/20 rounded-full px-6 py-3 mb-8">
            <Search className="h-5 w-5 text-secondary" />
            <span className="text-secondary font-semibold">Encontre o profissional ideal</span>
          </div>
          
          <h2 className="text-5xl md:text-6xl font-bold mb-8 bg-gradient-to-r from-white via-secondary to-white bg-clip-text text-transparent">
            Cadastre sua demanda
          </h2>
          
          <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Descreva o que você precisa e receba propostas personalizadas de profissionais qualificados em minutos.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <Zap className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Rápido e fácil</h3>
            <p className="text-gray-400 leading-relaxed">
              Publique sua demanda em menos de 2 minutos
            </p>
          </div>

          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <Clock className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Propostas em minutos</h3>
            <p className="text-gray-400 leading-relaxed">
              Receba múltiplas propostas de profissionais interessados
            </p>
          </div>

          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <CheckCircle className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Escolha o melhor</h3>
            <p className="text-gray-400 leading-relaxed">
              Compare preços, avaliações e escolha o profissional ideal
            </p>
          </div>
        </div>
          </div>
        <div className="text-center">
          <button
            onClick={() => navigate('/post-demand')}
            className="group bg-secondary hover:bg-secondary/90 text-black px-12 py-6 rounded-2xl font-bold text-xl transition-all duration-300 hover:transform hover:scale-105 hover:shadow-2xl hover:shadow-secondary/25 inline-flex items-center gap-4"
          >
            Publicar demanda
            <ArrowRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" />
          </button>
          
          <div className="mt-8 flex items-center justify-center gap-8 text-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>100% gratuito</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>Sem compromisso</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>Resposta rápida</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}