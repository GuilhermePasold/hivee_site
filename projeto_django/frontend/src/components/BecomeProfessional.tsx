import React from 'react';
import { ArrowRight, Users, TrendingUp, Shield, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function BecomeProfessional() {
  const navigate = useNavigate();

  return (
    <div className="relative py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-secondary/10 backdrop-blur-sm border border-secondary/20 rounded-full px-6 py-3 mb-8">
            <Users className="h-5 w-5 text-secondary" />
            <span className="text-secondary font-semibold">Junte-se à nossa comunidade</span>
          </div>
          
          <h2 className="text-5xl md:text-6xl font-bold mb-8 bg-gradient-to-r from-white via-secondary to-white bg-clip-text text-transparent">
            Seja um prestador de serviços
          </h2>
          
          <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Transforme suas habilidades em oportunidades. Alcance milhares de clientes e construa uma carreira de sucesso na maior plataforma de serviços do Brasil.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <TrendingUp className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Aumente sua renda</h3>
            <p className="text-gray-400 leading-relaxed">
              Profissionais ganham em média 40% mais através da nossa plataforma
            </p>
          </div>

          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <Shield className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Pagamentos seguros</h3>
            <p className="text-gray-400 leading-relaxed">
              Sistema de pagamento protegido com garantia de recebimento
            </p>
          </div>

          <div className="group bg-zinc-900/30 backdrop-blur-sm border border-zinc-800 p-8 rounded-2xl hover:border-secondary/30 transition-all duration-300 hover:transform hover:scale-105">
            <div className="bg-secondary/10 p-4 rounded-2xl w-fit mb-6 group-hover:bg-secondary/20 transition-colors">
              <Star className="h-8 w-8 text-secondary" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Construa reputação</h3>
            <p className="text-gray-400 leading-relaxed">
              Sistema de avaliações que valoriza seu trabalho de qualidade
            </p>
          </div>
        </div>

        <div className="text-center">
          <button 
            onClick={() => navigate('/become-professional')}
            className="group bg-secondary hover:bg-secondary/90 text-black px-12 py-6 rounded-2xl font-bold text-xl transition-all duration-300 hover:transform hover:scale-105 hover:shadow-2xl hover:shadow-secondary/25 inline-flex items-center gap-4"
          >
            Cadastre-se como profissional
            <ArrowRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" />
          </button>
          
          <div className="mt-8 flex items-center justify-center gap-8 text-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>Cadastro gratuito</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>Suporte 24/7</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full"></div>
              <span>Sem taxas de adesão</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}