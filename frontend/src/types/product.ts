export interface Product {
  id: string;
  name: string;
  brand: string;
  price: number;
  originalPrice?: number;
  image: string;
  rating: number;
  retailer: string;
  delivery: string;
  matchScore: number;
  whySuggested: string;
  category: string;
  alternatives: { id: string; name: string; price: number; brand: string }[];
}
