import React from 'react';
import { Trophy } from 'lucide-react';

interface AchievementCardProps {
  title: string;
  description: string;
  progress: number;
  maxProgress: number;
  achieved: boolean;
}

export function AchievementCard({ title, description, progress, maxProgress, achieved }: AchievementCardProps) {
  const progressPercentage = (progress / maxProgress) * 100;

  return (
    <div className={`bg-primary-light p-6 rounded-lg ${achieved ? 'border-2 border-secondary' : ''}`}>
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-full ${achieved ? 'bg-secondary' : 'bg-gray-700'}`}>
          <Trophy className={`h-6 w-6 ${achieved ? 'text-black' : 'text-gray-400'}`} />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
          <p className="text-gray-400 text-sm mb-3">{description}</p>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-secondary rounded-full h-2 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <p className="text-gray-400 text-sm mt-2">
            {progress} / {maxProgress}
          </p>
        </div>
      </div>
    </div>
  );
}