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

const inferCategory = (title: string): string => {
  const lower = title.toLowerCase();
  if (lower.includes("t-shirt") || lower.includes("tshirt") || lower.includes("tee")) return "t-shirt";
  if (lower.includes("shirt")) return "t-shirt";
  if (lower.includes("pants") || lower.includes("jeans") || lower.includes("trouser")) return "pants";
  if (lower.includes("shorts")) return "shorts";
  if (lower.includes("dress")) return "dress";
  if (lower.includes("skirt")) return "skirt";
  if (lower.includes("hoodie") || lower.includes("sweater")) return "tops";
  if (lower.includes("shoe") || lower.includes("sneaker") || lower.includes("boot")) return "shoes";
  if (lower.includes("bag") || lower.includes("backpack") || lower.includes("purse")) return "bag";
  return "apparel";
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
    size: item.variant.size || "",
    url: item.link || undefined,
    rating: item.verified ? 4.8 : 4.5,
    retailer: item.retailer,
    delivery,
    matchScore: item.verified ? 96 : 90,
    whySuggested,
    category: inferCategory(item.title),
    alternatives: [],
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
