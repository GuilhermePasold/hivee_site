import React from 'react';
import { Star, Award } from 'lucide-react';
import { Review } from '../../types';

interface ProfessionalReviewsProps {
  reviews: Review[];
}

export function ProfessionalReviews({ reviews }: ProfessionalReviewsProps) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <Award className="h-5 w-5 text-secondary" />
        Avaliações Recentes
      </h2>
      <div className="space-y-6">
        {reviews.map(review => (
          <div key={review.id} className="border-b border-gray-700 pb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-semibold">{review.author}</span>
              <div className="flex items-center">
                {Array.from({ length: review.rating }).map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 text-secondary fill-current"
                  />
                ))}
              </div>
            </div>
            <p className="text-gray-300">{review.comment}</p>
            <p className="text-gray-400 text-sm mt-2">
              {new Date(review.date).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}