import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
  Home, 
  User, 
  Briefcase, 
  Settings, 
  HelpCircle, 
  HeadphonesIcon,
  UserPlus,
  FileText,
  Handshake
} from 'lucide-react';

interface SideMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SideMenu({ isOpen, onClose }: SideMenuProps) {
  const navigate = useNavigate();

  const menuItems = [
    { icon: Home, label: 'Início', path: '/' },
    { icon: Briefcase, label: 'Serviços', path: '/services' },
    { icon: Briefcase, label: 'Meus Serviços', path: '/my-services' },
    { icon: User, label: 'Meu Perfil', path: '/profile' },
    { icon: Handshake, label: 'Match de Serviços', path: '/service-match' },
    { icon: UserPlus, label: 'Seja um Prestador', path: '/become-professional' },
    { icon: FileText, label: 'Cadastre sua Demanda', path: '/post-demand' },
    { icon: HelpCircle, label: 'Como Funciona', path: '/how-it-works' },
    { icon: Settings, label: 'Configurações', path: '/settings' },
    { icon: HeadphonesIcon, label: 'Suporte', path: '/support' },
    { icon: HelpCircle, label: 'Ajuda', path: '/help' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <>
      <div 
        className={`fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`} 
        onClick={onClose} 
      />
      <div 
        className={`fixed inset-y-0 left-0 w-64 bg-primary-light z-50 shadow-lg transform transition-transform duration-300 ease-in-out overflow-hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 flex justify-between items-center border-b border-gray-800">
          <h2 className="text-white text-xl font-bold">Menu</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>
        <nav className="p-4 overflow-y-auto h-full">
          <div className="space-y-1">
            {menuItems.map((item, index) => (
              <button
                key={index}
                className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-primary rounded-lg transition-colors"
                onClick={() => handleNavigation(item.path)}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                <span className="truncate">{item.label}</span>
              </button>
            ))}
          </div>
        </nav>
      </div>
    </>
  );
}