import React, { useState, useRef, useEffect } from 'react';
import { MapPin } from 'lucide-react';
import { locations } from '../data/locations';
import { Location } from '../types';

interface LocationSelectorProps {
  onLocationSelect: (location: Location | null) => void;
  selectedLocation: Location | null;
}

export function LocationSelector({ onLocationSelect, selectedLocation }: LocationSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredLocations = locations.filter(location => 
    `${location.city} ${location.state} ${location.neighborhood}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 bg-primary-light rounded-l-lg text-white hover:bg-opacity-80 transition-colors"
      >
        <MapPin className="h-5 w-5 text-secondary" />
        <span className="text-sm">
          {selectedLocation 
            ? `${selectedLocation.neighborhood}, ${selectedLocation.city}`
            : 'Selecionar local'}
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 w-72 bg-primary-light rounded-lg shadow-lg">
          <div className="p-2">
            <input
              type="text"
              placeholder="Buscar localização..."
              className="w-full px-3 py-2 bg-primary text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="max-h-60 overflow-y-auto">
            {filteredLocations.map((location) => (
              <button
                key={location.id}
                className="w-full px-4 py-2 text-left text-white hover:bg-primary transition-colors"
                onClick={() => {
                  onLocationSelect(location);
                  setIsOpen(false);
                }}
              >
                {location.neighborhood}, {location.city} - {location.state}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}