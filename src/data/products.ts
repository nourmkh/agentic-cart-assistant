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

export const mockProducts: Product[] = [
  {
    id: "1",
    name: "AirPods Max Pro",
    brand: "Apple",
    price: 349,
    originalPrice: 549,
    image: "headphones",
    rating: 4.8,
    retailer: "Amazon",
    delivery: "Free · Tomorrow",
    matchScore: 97,
    whySuggested: "Best noise-cancelling in your budget. 36% off today. Top-rated across 12K+ reviews. Matches your preference for premium audio.",
    category: "Electronics",
    alternatives: [
      { id: "1a", name: "Sony WH-1000XM5", price: 298, brand: "Sony" },
      { id: "1b", name: "Bose QC Ultra", price: 329, brand: "Bose" },
      { id: "1c", name: "Sennheiser Momentum 4", price: 279, brand: "Sennheiser" },
    ],
  },
  {
    id: "2",
    name: "UltraBoost Light 24",
    brand: "Adidas",
    price: 119,
    originalPrice: 190,
    image: "sneakers",
    rating: 4.6,
    retailer: "Nike.com",
    delivery: "Free · 2 days",
    matchScore: 94,
    whySuggested: "Best value running shoe. 37% off. Top pick for daily runners. Matches your sporty style preference.",
    category: "Footwear",
    alternatives: [
      { id: "2a", name: "Nike Pegasus 41", price: 130, brand: "Nike" },
      { id: "2b", name: "New Balance 1080v13", price: 149, brand: "New Balance" },
      { id: "2c", name: "ASICS Gel-Nimbus 26", price: 140, brand: "ASICS" },
    ],
  },
  {
    id: "3",
    name: "Pixel Watch 3",
    brand: "Google",
    price: 279,
    image: "watch",
    rating: 4.5,
    retailer: "Best Buy",
    delivery: "Free · 3 days",
    matchScore: 91,
    whySuggested: "Best health tracking in price range. Seamless integration with your phone. Top AI features for fitness.",
    category: "Wearables",
    alternatives: [
      { id: "3a", name: "Apple Watch SE", price: 249, brand: "Apple" },
      { id: "3b", name: "Samsung Galaxy Watch 7", price: 299, brand: "Samsung" },
      { id: "3c", name: "Garmin Venu 3", price: 329, brand: "Garmin" },
    ],
  },
  {
    id: "4",
    name: "Metro Crossbody",
    brand: "Everlane",
    price: 78,
    originalPrice: 98,
    image: "bag",
    rating: 4.7,
    retailer: "Everlane",
    delivery: "Free · 4 days",
    matchScore: 88,
    whySuggested: "Trending crossbody style. Sustainable materials match your eco-preference. Great reviews for daily carry.",
    category: "Accessories",
    alternatives: [
      { id: "4a", name: "Baggu Crescent Bag", price: 52, brand: "Baggu" },
      { id: "4b", name: "Aer City Sling 2", price: 89, brand: "Aer" },
      { id: "4c", name: "Bellroy Sling", price: 99, brand: "Bellroy" },
    ],
  },
];

export const agentLogs = [
  { step: 1, action: "Parsed query", detail: "Identified 4 product categories from your request", time: "0.2s" },
  { step: 2, action: "Scanned retailers", detail: "Searched across Amazon, Best Buy, Nike, Everlane + 12 more", time: "1.1s" },
  { step: 3, action: "Ranked 847 items", detail: "Applied budget, style, and delivery filters", time: "0.8s" },
  { step: 4, action: "Price optimized", detail: "Found $312 in savings across your cart", time: "0.3s" },
  { step: 5, action: "Verified availability", detail: "All items in stock with guaranteed delivery dates", time: "0.5s" },
  { step: 6, action: "Cart assembled", detail: "Top-ranked items selected. Ready for review.", time: "0.1s" },
];
