import React, { useState } from 'react';
import { MapPin, Loader2, Search, X } from 'lucide-react';
import { LocationResult } from '../types';
import { searchLocations } from '../utils/geocoding';
import { useLocationStore } from '../stores/locationStore';

interface SearchLocationProps {
  className?: string;
}

export function SearchLocation({ className = '' }: SearchLocationProps) {
  const [locationQuery, setLocationQuery] = useState('');
  const [locationResults, setLocationResults] = useState<LocationResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const { setSelectedLocation, searchQuery, setSearchQuery } = useLocationStore();

  const handleLocationSearch = async (query: string) => {
    setLocationQuery(query);

    if (query.length > 2) {
      setIsLoading(true);
      const results = await searchLocations(query);
      setLocationResults(results);
      setShowResults(true);
      setIsLoading(false);
      return;
    }

    setLocationResults([]);
    setShowResults(false);
  };

  const handleLocationSelect = (location: LocationResult) => {
    setSelectedLocation(location);
    setLocationQuery(location.display_name);
    setShowResults(false);
  };

  const clearFilters = () => {
    setSelectedLocation(null);
    setLocationQuery('');
    setSearchQuery('');
    setLocationResults([]);
    setShowResults(false);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="grid gap-3 rounded-xl bg-primary-light p-3 shadow-lg border border-white/5 focus-within:border-secondary/50 transition-colors md:grid-cols-[1fr_1fr_auto]">
        <div className="flex h-12 items-center rounded-lg bg-black/20 px-3">
          <Search className="h-5 w-5 text-secondary mr-3 flex-shrink-0" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Busque por servico, profissional ou categoria"
            className="w-full min-w-0 bg-transparent text-white placeholder-gray-400 focus:outline-none"
          />
        </div>

        <div className="relative">
          <div className="flex h-12 items-center rounded-lg bg-black/20 px-3">
            <MapPin className="h-5 w-5 text-secondary mr-3 flex-shrink-0" />
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => handleLocationSearch(e.target.value)}
              placeholder="Localizacao"
              className="w-full min-w-0 bg-transparent text-white placeholder-gray-400 focus:outline-none"
            />
            {isLoading && (
              <Loader2 className="h-5 w-5 text-secondary ml-3 animate-spin flex-shrink-0" />
            )}
          </div>

          {showResults && locationResults.length > 0 && (
            <div className="absolute z-50 mt-2 w-full bg-primary-light border border-white/10 rounded-lg shadow-2xl max-h-60 overflow-y-auto">
              {locationResults.map((location, index) => (
                <button
                  key={index}
                  className="w-full px-6 py-3 text-left text-white hover:bg-white/10 transition-colors border-b border-white/5 last:border-b-0"
                  onClick={() => handleLocationSelect(location)}
                >
                  {location.display_name}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={clearFilters}
          className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-white/10 px-4 text-white hover:border-secondary/50 hover:text-secondary transition-colors"
          aria-label="Limpar busca"
        >
          <X className="h-5 w-5" />
          <span className="md:hidden lg:inline">Limpar</span>
        </button>
      </div>
    </div>
  );
}
