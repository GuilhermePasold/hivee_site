import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { FadeInSection } from '../components/FadeInSection';
import { ChevronDown, ChevronUp, HelpCircle, MessageSquare, Phone, Mail } from 'lucide-react';
import { SocialButtons } from '../components/SocialButtons';

const faqs = [
  {
    question: 'Como funciona o HIVEE?',
    answer: 'O HIVEE é uma plataforma que conecta profissionais qualificados a clientes que precisam de serviços. Você pode buscar profissionais por categoria, verificar avaliações e fazer contratações de forma segura.'
  },
  {
    question: 'Como posso me tornar um prestador de serviços?',
    answer: 'Para se tornar um prestador, clique em "Seja um Prestador" no menu, preencha o formulário de cadastro com suas informações e documentos necessários. Após a aprovação, você poderá começar a receber demandas.'
  },
  {
    question: 'Como funciona o pagamento?',
    answer: 'O HIVEE oferece diferentes formas de pagamento seguras. O valor é retido até a conclusão do serviço, garantindo segurança tanto para o cliente quanto para o prestador.'
  },
  {
    question: 'Como avalio um serviço?',
    answer: 'Após a conclusão do serviço, você receberá uma notificação para avaliar o prestador. Você pode dar uma nota de 1 a 5 estrelas e deixar um comentário sobre sua experiência.'
  },
  {
    question: 'O que fazer se tiver problemas com um serviço?',
    answer: 'Em caso de problemas, entre em contato com nosso suporte 24/7. Temos uma equipe dedicada para resolver qualquer situação e garantir sua satisfação.'
  },
  {
    question: 'Como funciona a garantia dos serviços?',
    answer: 'Todos os serviços têm garantia de 30 dias. Se houver qualquer problema, o prestador deverá resolver sem custos adicionais.'
  }
];

export function HelpPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [openFaqs, setOpenFaqs] = useState<number[]>([]);

  const toggleFaq = (index: number) => {
    setOpenFaqs(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu isOpen={isSideMenuOpen} onClose={() => setIsSideMenuOpen(false)} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <div className="bg-gradient-to-br from-secondary/20 to-primary p-8 rounded-2xl mb-12">
            <div className="flex items-center gap-4 mb-6">
              <div className="bg-secondary p-3 rounded-full">
                <HelpCircle className="h-6 w-6 text-black" />
              </div>
              <h1 className="text-3xl font-bold text-white">Central de Ajuda</h1>
            </div>
            <p className="text-xl text-gray-300">
              Encontre respostas para suas dúvidas mais frequentes
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-primary-light p-6 rounded-xl text-center hover:transform hover:scale-105 transition-all duration-300">
              <MessageSquare className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Chat Online</h2>
              <p className="text-gray-400">Disponível 24/7</p>
            </div>

            <div className="bg-primary-light p-6 rounded-xl text-center hover:transform hover:scale-105 transition-all duration-300">
              <Phone className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Telefone</h2>
              <p className="text-gray-400">0800 123 4567</p>
            </div>

            <div className="bg-primary-light p-6 rounded-xl text-center hover:transform hover:scale-105 transition-all duration-300">
              <Mail className="h-8 w-8 text-secondary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Email</h2>
              <p className="text-gray-400">suporte@hivee.com</p>
            </div>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="bg-primary-light rounded-xl overflow-hidden transition-all duration-300 hover:shadow-lg"
              >
                <button
                  className="w-full px-6 py-4 flex justify-between items-center text-left"
                  onClick={() => toggleFaq(index)}
                >
                  <span className="text-lg font-semibold text-white">{faq.question}</span>
                  {openFaqs.includes(index) ? (
                    <ChevronUp className="h-5 w-5 text-secondary" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-secondary" />
                  )}
                </button>
                {openFaqs.includes(index) && (
                  <div className="px-6 pb-4">
                    <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}