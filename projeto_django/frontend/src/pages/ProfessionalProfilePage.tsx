import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import {
  Star,
  Award,
  Calendar,
  MapPin,
  Clock,
  GraduationCap,
} from 'lucide-react';
import { ProfessionalInfo } from '../components/professional/ProfessionalInfo';
import { ProfessionalCertifications } from '../components/professional/ProfessionalCertifications';
import { ProfessionalReviews } from '../components/professional/ProfessionalReviews';
import { useProfessionalData } from '../hooks/useProfessionalData';
import { SocialButtons } from '../components/SocialButtons';

export function ProfessionalProfilePage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const professional = useProfessionalData();

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <div className="bg-primary-light rounded-lg overflow-hidden">
            <div className="relative h-64">
              <img
                src={professional.image}
                alt={professional.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-6">
                <h1 className="text-3xl font-bold text-white">
                  {professional.name}
                </h1>
                <p className="text-gray-300">{professional.title}</p>
              </div>
            </div>

            <div className="p-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <ProfessionalInfo professional={professional} />
                  <ProfessionalCertifications
                    certifications={professional.certifications}
                  />
                </div>
                <ProfessionalReviews reviews={professional.reviews} />
              </div>

              <div className="mt-8 flex justify-center">
                <button className="bg-secondary text-black px-8 py-4 rounded-lg font-semibold hover:bg-secondary-light transition-colors">
                  Contratar Profissional • R$ {professional.price}/hora
                </button>
              </div>
            </div>
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
