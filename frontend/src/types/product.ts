export interface Product {
  id: string;
  name: string;
  brand: string;
  price: number;
  size: string;
  /** Local asset key (e.g. "headphones") or full image URL (Zara, Stradivarius, etc.) */
  image: string;
  /** Product page URL on retailer site (e.g. Zara, Stradivarius) */
  url?: string;
  rating: number;
  retailer: string;
  delivery: string;
  matchScore: number;
  whySuggested: string;
  category: string;
  alternatives: { id: string; name: string; price: number; brand: string }[];
}
