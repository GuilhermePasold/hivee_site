import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Hero } from '../components/Hero';
import { CategoryList } from '../components/CategoryList';
import { ProfessionalCarousel } from '../components/ProfessionalCarousel';
import { BecomeProfessional } from '../components/BecomeProfessional';
import { PostDemand } from '../components/PostDemand';
import { Testimonials } from '../components/Testimonials';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { useLocationStore } from '../stores/locationStore';
import { SocialButtons } from '../components/SocialButtons';

export function HomePage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const { selectedLocation } = useLocationStore();

  return (
    <div className="min-h-screen relative">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />
      <Hero />

      {/* Main content sections */}
      <main className="relative z-10">
        <>
          <FadeInSection>
            <section className="py-24 relative">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                  <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                    Explore por categoria
                  </h2>
                  <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    Encontre exatamente o que você precisa
                  </p>
                </div>
                <CategoryList />
              </div>
            </section>
          </FadeInSection>

          <FadeInSection delay={200}>
            <section className="py-24 relative">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                  <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                    Prestadores em destaque
                  </h2>
                  <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    Profissionais altamente avaliados na sua região
                  </p>
                </div>
                <ProfessionalCarousel />
              </div>
            </section>
          </FadeInSection>
        </>


        <FadeInSection delay={300}>
          <BecomeProfessional />
        </FadeInSection>

        <FadeInSection delay={400}>
          <PostDemand />
        </FadeInSection>

        <FadeInSection delay={500}>
          <Testimonials />
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}