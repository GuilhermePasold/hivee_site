import React, { useState, useRef, useEffect } from 'react';
import { Search, MapPin, Loader2 } from 'lucide-react';
import { LocationResult } from '../types';
import { searchLocations } from '../utils/geocoding';

interface SearchBarProps {
  onSearch: (query: string, location: LocationResult | null) => void;
}

export function SearchBar({ onSearch }: SearchBarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [selectedLocation, setSelectedLocation] = useState<LocationResult | null>(null);
  const [locationResults, setLocationResults] = useState<LocationResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const locationDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (locationDropdownRef.current && !locationDropdownRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const searchTimer = setTimeout(async () => {
      if (locationQuery) {
        setIsLoading(true);
        const results = await searchLocations(locationQuery);
        setLocationResults(results);
        setShowResults(true);
        setIsLoading(false);
      } else {
        setLocationResults([]);
        setShowResults(false);
      }
    }, 300);

    return () => clearTimeout(searchTimer);
  }, [locationQuery]);

  const handleSearch = () => {
    onSearch(searchQuery, selectedLocation);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && selectedLocation) {
      handleSearch();
    }
  };

  const handleLocationSelect = (location: LocationResult) => {
    setSelectedLocation(location);
    setLocationQuery(location.display_name);
    setShowResults(false);
  };

  return (
    <div className="flex flex-col sm:flex-row gap-2">
      <div className="relative flex-1" ref={locationDropdownRef}>
        <div className="flex items-center bg-primary-light rounded-lg">
          <MapPin className="h-5 w-5 text-secondary ml-3" />
          <input
            type="text"
            value={locationQuery}
            onChange={(e) => setLocationQuery(e.target.value)}
            placeholder="Digite uma localização..."
            className="w-full px-3 py-2 bg-transparent text-white placeholder-gray-400 focus:outline-none"
          />
          {isLoading && <Loader2 className="h-5 w-5 text-secondary mr-3 animate-spin" />}
        </div>

        {showResults && locationResults.length > 0 && (
          <div className="absolute z-50 mt-2 w-full bg-primary-light rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {locationResults.map((location, index) => (
              <button
                key={index}
                className="w-full px-4 py-2 text-left text-white hover:bg-primary transition-colors"
                onClick={() => handleLocationSelect(location)}
              >
                {location.display_name}
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedLocation && (
        <div className="relative flex-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Buscar serviços..."
            className="w-full px-4 py-2 rounded-lg bg-primary-light text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-secondary"
          />
          <button
            onClick={handleSearch}
            className="absolute right-3 top-2.5 text-gray-400 hover:text-secondary"
          >
            <Search className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}