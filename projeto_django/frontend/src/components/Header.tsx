import React, { useState, useEffect } from 'react';
import { Menu, Search, Bell, User } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Logo } from './Logo';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Show/hide header based on scroll direction
      if (currentScrollY > lastScrollY && currentScrollY > 150) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }
      
      // Background blur effect
      setIsScrolled(currentScrollY > 50);
      setLastScrollY(currentScrollY);
    };

    let ticking = false;
    const handleScrollThrottled = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScrollThrottled, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const navItems = [
    { label: 'Início', path: '/' },
    { label: 'Serviços', path: '/services' },
    { label: 'Como funciona', path: '/how-it-works' },
    { label: 'Suporte', path: '/support' },
  ];

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      } ${
        isScrolled 
          ? 'bg-black/20 backdrop-blur-2xl border-b border-white/5' 
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Logo />

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                  location.pathname === item.path
                    ? 'bg-secondary/20 text-secondary border border-secondary/30'
                    : 'text-gray-300 hover:text-white hover:bg-white/5'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-3">
            {/* Search Button */}
            <button className="hidden md:flex items-center justify-center w-10 h-10 rounded-full bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 hover:border-secondary/30 transition-all duration-300 group">
              <Search className="h-5 w-5 text-gray-300 group-hover:text-secondary transition-colors" />
            </button>

            {/* Notifications */}
            <button className="hidden md:flex items-center justify-center w-10 h-10 rounded-full bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 hover:border-secondary/30 transition-all duration-300 group relative">
              <Bell className="h-5 w-5 text-gray-300 group-hover:text-secondary transition-colors" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-black"></div>
            </button>

            {/* Menu Button */}
            <button 
              onClick={onMenuClick}
              className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 hover:border-secondary/30 transition-all duration-300 group"
            >
              <Menu className="h-5 w-5 text-gray-300 group-hover:text-secondary transition-colors" />
            </button>

            {/* Login Button */}
            <button 
              onClick={() => navigate('/login')}
              className="flex items-center gap-2 bg-secondary hover:bg-secondary/90 text-black px-6 py-2.5 rounded-full font-semibold transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-secondary/25"
            >
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Entrar</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}