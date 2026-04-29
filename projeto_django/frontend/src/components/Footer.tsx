import React from 'react';
import { Logo } from './Logo';
import { Instagram, Facebook, Linkedin, Mail, Phone, MapPin, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Footer() {
  const navigate = useNavigate();

  const footerLinks = {
    services: [
      { label: 'Limpeza', path: '/category/1' },
      { label: 'Montagem', path: '/category/2' },
      { label: 'Elétrica', path: '/category/3' },
      { label: 'Jardinagem', path: '/category/6' },
    ],
    company: [
      { label: 'Sobre nós', path: '/about' },
      { label: 'Como funciona', path: '/how-it-works' },
      { label: 'Seja um prestador', path: '/become-professional' },
      { label: 'Carreiras', path: '/careers' },
    ],
    support: [
      { label: 'Central de Ajuda', path: '/help' },
      { label: 'Suporte', path: '/support' },
      { label: 'Contato', path: '/contact' },
      { label: 'Status do Sistema', path: '/status' },
    ],
    legal: [
      { label: 'Termos de Uso', path: '/terms' },
      { label: 'Privacidade', path: '/privacy' },
      { label: 'Cookies', path: '/cookies' },
      { label: 'Segurança', path: '/security' },
    ],
  };

  return (
    <footer className="relative bg-black/20 backdrop-blur-2xl border-t border-white/5">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent pointer-events-none" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-12 mb-12">
          {/* Brand Section */}
          <div className="lg:col-span-2 space-y-6">
            <Logo />
            <p className="text-gray-400 text-lg leading-relaxed max-w-md">
              Conectamos você aos melhores profissionais da sua região com segurança, qualidade e rapidez.
            </p>
            
            {/* Contact Info */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-gray-400 hover:text-white transition-colors">
                <Mail className="h-5 w-5 text-secondary" />
                <span>contato@hivee.com</span>
              </div>
              <div className="flex items-center gap-3 text-gray-400 hover:text-white transition-colors">
                <Phone className="h-5 w-5 text-secondary" />
                <span>0800 123 4567</span>
              </div>
              <div className="flex items-center gap-3 text-gray-400 hover:text-white transition-colors">
                <MapPin className="h-5 w-5 text-secondary" />
                <span>Caçador, SC</span>

              </div>
            </div>

            {/* Social Links */}
            <div className="flex space-x-4">
              {[
                { icon: Instagram, href: 'https://instagram.com/hivee', label: 'Instagram' },
                { icon: Facebook, href: 'https://facebook.com/hivee', label: 'Facebook' },
                { icon: Linkedin, href: 'https://linkedin.com/company/hivee', label: 'LinkedIn' },
              ].map(({ icon: Icon, href, label }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center w-12 h-12 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full hover:bg-secondary hover:border-secondary hover:text-black transition-all duration-300 hover:scale-110 group"
                  aria-label={label}
                >
                  <Icon className="h-5 w-5 text-gray-400 group-hover:text-black transition-colors" />
                </a>
              ))}
            </div>
          </div>

          {/* Links Sections */}
          <div className="grid grid-cols-2 lg:grid-cols-3 lg:col-span-3 gap-8">
            <div>
              <h3 className="text-white font-semibold mb-6 text-lg">Serviços</h3>
              <ul className="space-y-3">
                {footerLinks.services.map((link) => (
                  <li key={link.path}>
                    <button
                      onClick={() => navigate(link.path)}
                      className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2 group"
                    >
                      <span>{link.label}</span>
                      <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-white font-semibold mb-6 text-lg">Empresa</h3>
              <ul className="space-y-3">
                {footerLinks.company.map((link) => (
                  <li key={link.path}>
                    <button
                      onClick={() => navigate(link.path)}
                      className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2 group"
                    >
                      <span>{link.label}</span>
                      <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="col-span-2 lg:col-span-1">
              <h3 className="text-white font-semibold mb-6 text-lg">Suporte</h3>
              <ul className="space-y-3 mb-6">
                {footerLinks.support.map((link) => (
                  <li key={link.path}>
                    <button
                      onClick={() => navigate(link.path)}
                      className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2 group"
                    >
                      <span>{link.label}</span>
                      <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  </li>
                ))}
              </ul>
              
              <h4 className="text-white font-semibold mb-3">Legal</h4>
              <ul className="space-y-2">
                {footerLinks.legal.map((link) => (
                  <li key={link.path}>
                    <button
                      onClick={() => navigate(link.path)}
                      className="text-gray-400 hover:text-white transition-colors text-xs flex items-center gap-2 group"
                    >
                      <span>{link.label}</span>
                      <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-500 text-sm">
            © 2024 HIVEE. Todos os direitos reservados.
          </p>
          
          <div className="flex items-center gap-6 text-xs text-gray-500">
            <span>Feito com ❤️ no Brasil</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Todos os sistemas operacionais</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}