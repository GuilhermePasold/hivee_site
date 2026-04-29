import { create } from 'zustand';
import { LocationResult } from '../types';

interface LocationStore {
  selectedLocation: LocationResult | null;
  setSelectedLocation: (location: LocationResult | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export const useLocationStore = create<LocationStore>((set) => ({
  selectedLocation: null,
  setSelectedLocation: (location) => set({ selectedLocation: location }),
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
}));