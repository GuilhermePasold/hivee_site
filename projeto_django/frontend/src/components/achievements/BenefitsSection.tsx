import React from 'react';
import { AchievementCard } from './AchievementCard';
import { FadeInSection } from '../FadeInSection';

const achievements = [
  {
    title: 'Profissional Iniciante',
    description: 'Complete 10 serviços com avaliação positiva',
    progress: 7,
    maxProgress: 10,
    achieved: false,
  },
  {
    title: 'Especialista',
    description: 'Receba 50 avaliações 5 estrelas',
    progress: 50,
    maxProgress: 50,
    achieved: true,
  },
  {
    title: 'Cliente Fiel',
    description: 'Tenha 5 clientes recorrentes',
    progress: 3,
    maxProgress: 5,
    achieved: false,
  },
  {
    title: 'Pontualidade Perfeita',
    description: 'Complete 20 serviços no prazo',
    progress: 20,
    maxProgress: 20,
    achieved: true,
  },
];

export function BenefitsSection() {
  return (
    <FadeInSection>
      <div className="bg-primary-light p-8 rounded-lg">
        <h2 className="text-2xl font-bold text-white mb-6">Meus Benefícios</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {achievements.map((achievement, index) => (
            <AchievementCard key={index} {...achievement} />
          ))}
        </div>
      </div>
    </FadeInSection>
  );
}