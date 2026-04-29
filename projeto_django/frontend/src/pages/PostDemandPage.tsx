import React, { useState } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { SideMenu } from '../components/SideMenu';
import { categories } from '../data/categories';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { FadeInSection } from '../components/FadeInSection';
import { SocialButtons } from '../components/SocialButtons';

export function PostDemandPage() {
  const [isSideMenuOpen, setIsSideMenuOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [budget, setBudget] = useState('');
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetch('http://127.0.0.1:8000/api/post-demand/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title,
        description,
        category,
        budget,
        date: selectedDate,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSuccessMessage(data.message);
          setTitle('');
          setDescription('');
          setCategory('');
          setBudget('');
          setSelectedDate(null);
        } else {
          setError(data.message || 'Erro ao publicar demanda');
        }
      })
      .catch((err) => {
        console.error('Erro de demanda:', err);
        setError('Erro de conexão com o servidor');
      });
  };


  return (
    <div className="min-h-screen bg-black">
      <Header onMenuClick={() => setIsSideMenuOpen(true)} />
      <SideMenu
        isOpen={isSideMenuOpen}
        onClose={() => setIsSideMenuOpen(false)}
      />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <FadeInSection>
          <h1 className="text-3xl font-bold text-white mb-8">
            Cadastrar Nova Demanda
          </h1>

          {error && (
            <div className="mb-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg p-3 text-sm text-center">
              {error}
            </div>
          )}
          {successMessage && (
            <div className="mb-4 bg-green-500/10 border border-green-500/30 text-green-500 rounded-lg p-3 text-sm text-center">
              {successMessage}
            </div>
          )}
          <form
            onSubmit={handleSubmit}
            className="space-y-6 bg-primary-light p-8 rounded-lg"
          >

            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium text-white mb-2"
              >
                Título da Demanda
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-primary border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                required
              />
            </div>

            <div>
              <label
                htmlFor="category"
                className="block text-sm font-medium text-white mb-2"
              >
                Categoria
              </label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-primary border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                required
              >
                <option value="">Selecione uma categoria</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="date"
                className="block text-sm font-medium text-white mb-2"
              >
                Data Preferencial
              </label>
              <DatePicker
                selected={selectedDate}
                onChange={(date) => setSelectedDate(date)}
                className="mt-1 block w-full px-3 py-2 bg-primary border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                dateFormat="dd/MM/yyyy"
                minDate={new Date()}
                placeholderText="Selecione uma data"
                required
              />
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-white mb-2"
              >
                Descrição Detalhada
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="mt-1 block w-full px-3 py-2 bg-primary border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                required
              />
            </div>

            <div>
              <label
                htmlFor="budget"
                className="block text-sm font-medium text-white mb-2"
              >
                Orçamento Estimado (R$)
              </label>
              <input
                type="number"
                id="budget"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-primary border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-secondary"
                required
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                className="px-6 py-3 bg-secondary text-black rounded-md hover:bg-secondary-light transition-colors font-semibold"
              >
                Publicar Demanda
              </button>
            </div>
          </form>
        </FadeInSection>
      </main>

      <Footer />
      <SocialButtons />
    </div>
  );
}
