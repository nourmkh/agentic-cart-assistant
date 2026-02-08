import type { Product } from "@/types/product";
import { apiGet, apiPost } from "./client";

export async function fetchProducts(): Promise<Product[]> {
  return apiGet<Product[]>("/api/products");
}

export async function fetchProduct(id: string): Promise<Product> {
  return apiGet<Product>(`/api/products/${id}`);
}

export interface SearchRequest {
  query: string;
  preferences: string[];
  budget?: number;
  max_delivery_days?: number;
}

export interface SearchResponse {
  query: string;
  preferences: string[];
  weights: {
    price: number;
    delivery: number;
    style: number;
  };
  results: Record<string, {
    category: string;
    weights: Record<string, number>;
    products: Array<{
      rank: number;
      product: Product;
      score: number;
      score_breakdown: Record<string, number>;
      explanation: string;
      llm_explanation: string;
    }>;
  }>;
}

export async function searchProducts(request: SearchRequest): Promise<SearchResponse> {
  return apiPost<SearchResponse>("/api/products/search", request);
}
