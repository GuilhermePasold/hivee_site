// Update the types file to include new interfaces
export interface Service {
  id: string;
  title: string;
  description: string;
  category: string;
  price: number;
  rating: number;
  reviewCount: number;
  image: string;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
}

export interface LocationResult {
  display_name: string;
  lat: string;
  lon: string;
}

export interface Certification {
  name: string;
  issuer: string;
  year: number;
}

export interface Review {
  id: string;
  author: string;
  rating: number;
  comment: string;
  date: string;
}

export interface Professional {
  id: string;
  name: string;
  title: string;
  rating: number;
  reviewCount: number;
  location: string;
  experience: string;
  price: number;
  availability: string;
  image: string;
  certifications: Certification[];
  reviews: Review[];
}