import React from 'react';
import { Instagram, Facebook, Linkedin } from 'lucide-react';

export function SocialButtons() {
  return (
    <div className="fixed bottom-8 right-8 flex flex-col gap-4 z-50">
      <a
        href="https://instagram.com"
        target="_blank"
        rel="noopener noreferrer"
        className="bg-secondary hover:bg-secondary-light text-black p-3 rounded-full transition-all duration-300 hover:scale-110 shadow-lg"
      >
        <Instagram className="h-6 w-6" />
      </a>
      <a
        href="https://facebook.com"
        target="_blank"
        rel="noopener noreferrer"
        className="bg-secondary hover:bg-secondary-light text-black p-3 rounded-full transition-all duration-300 hover:scale-110 shadow-lg"
      >
        <Facebook className="h-6 w-6" />
      </a>
      <a
        href="https://linkedin.com"
        target="_blank"
        rel="noopener noreferrer"
        className="bg-secondary hover:bg-secondary-light text-black p-3 rounded-full transition-all duration-300 hover:scale-110 shadow-lg"
      >
        <Linkedin className="h-6 w-6" />
      </a>
    </div>
  );
}