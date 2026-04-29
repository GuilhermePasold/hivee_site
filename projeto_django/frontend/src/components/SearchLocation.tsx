import React, { useState } from 'react';
import { MapPin, Loader2, Search } from 'lucide-react';
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

  const handleSearch = async (query: string) => {
    setLocationQuery(query);
    if (query.length > 2) {
      setIsLoading(true);
      const results = await searchLocations(query);
      setLocationResults(results);
      setShowResults(true);
      setIsLoading(false);
    } else {
      setLocationResults([]);
      setShowResults(false);
    }
  };

  const handleLocationSelect = (location: LocationResult) => {
    setSelectedLocation(location);
    setLocationQuery(location.display_name);
    setShowResults(false);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Location Input */}
      <div className="relative">
        <div className="flex items-center bg-primary-light rounded-lg p-4 shadow-lg border border-white/5 focus-within:border-secondary/50 transition-colors">
          <MapPin className="h-6 w-6 text-secondary mr-3" />
          <input
            type="text"
            value={locationQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Digite sua localização para encontrar profissionais..."
            className="w-full bg-transparent text-white text-lg placeholder-gray-400 focus:outline-none"
          />
          {isLoading && <Loader2 className="h-6 w-6 text-secondary ml-3 animate-spin" />}
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
    </div>
  );

}