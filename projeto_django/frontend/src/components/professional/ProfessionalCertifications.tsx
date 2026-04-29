import React from 'react';
import { GraduationCap } from 'lucide-react';
import { Certification } from '../../types';

interface ProfessionalCertificationsProps {
  certifications: Certification[];
}

export function ProfessionalCertifications({ certifications }: ProfessionalCertificationsProps) {
  return (
    <div className="mt-8">
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <GraduationCap className="h-5 w-5 text-secondary" />
        Certificações
      </h2>
      <div className="space-y-4">
        {certifications.map((cert, index) => (
          <div
            key={index}
            className="bg-primary p-4 rounded-lg border border-gray-700"
          >
            <h3 className="text-white font-semibold">{cert.name}</h3>
            <p className="text-gray-400">
              {cert.issuer} • {cert.year}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}