import type { Product } from "@/types/product";
import { apiGet } from "./client";

export async function fetchProducts(): Promise<Product[]> {
  return apiGet<Product[]>("/api/products");
}

export async function fetchProduct(id: string): Promise<Product> {
  return apiGet<Product>(`/api/products/${id}`);
}
