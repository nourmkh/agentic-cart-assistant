import type { Product } from "@/types/product";
import { apiGet } from "./client";

interface CartItem {
  id: string;
  title: string;
  price: number;
  currency: string;
  image: string | null;
  retailer: string;
  deliveryEstimate: string;
  shortDescription?: string | null;
  variant: {
    size: string;
    color: string;
    material: string;
  };
  link: string | null;
  verified: boolean;
}

interface CartResponse {
  items: CartItem[];
  totalPrice: number;
}

const imageForItem = (item: CartItem): Product["image"] => {
  if (item.image) return item.image;
  const lower = item.title.toLowerCase();
  if (lower.includes("shoe") || lower.includes("sneaker") || lower.includes("boot")) {
    return "sneakers";
  }
  if (lower.includes("watch")) {
    return "watch";
  }
  if (lower.includes("bag") || lower.includes("backpack") || lower.includes("purse")) {
    return "bag";
  }
  return "bag";
};

const buildAlternatives = (item: CartItem): Product["alternatives"] => {
  const base = item.price || 0;
  return [
    { id: `${item.id}-alt1`, name: item.title, price: Math.max(0, base * 0.9), brand: item.retailer },
    { id: `${item.id}-alt2`, name: item.title, price: base * 1.05, brand: item.retailer },
    { id: `${item.id}-alt3`, name: item.title, price: base * 1.1, brand: item.retailer },
  ];
};

const mapCartItemToProduct = (item: CartItem): Product => {
  const delivery = item.deliveryEstimate || "";
  const variantParts = [item.variant.size, item.variant.color, item.variant.material].filter(Boolean).join(", ");
  const whySuggested = item.shortDescription || (variantParts ? `Matches your preferences (${variantParts}).` : "");

  return {
    id: item.id,
    name: item.title,
    brand: item.retailer,
    price: item.price,
    image: imageForItem(item),
    rating: item.verified ? 4.8 : 4.5,
    retailer: item.retailer,
    delivery,
    matchScore: item.verified ? 96 : 90,
    whySuggested,
    category: "Apparel",
    alternatives: buildAlternatives(item),
  };
};

export async function fetchProducts(): Promise<Product[]> {
  const response = await apiGet<CartResponse>("/api/cart");
  return response.items.map(mapCartItemToProduct);
}

export async function fetchProduct(id: string): Promise<Product> {
  const response = await apiGet<CartResponse>("/api/cart");
  const product = response.items.map(mapCartItemToProduct).find((item) => item.id === id);
  if (!product) throw new Error("Product not found");
  return product;
}
