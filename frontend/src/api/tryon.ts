import { apiPost } from "@/api/client";

export interface TryOnItem {
  image_url?: string;
  mask_url?: string;
  category?: string;
  sub_category?: string;
  body_region?: string;
}

export interface TryOnRequest {
  body_image_url: string;
  clothing_items: TryOnItem[];
}

export interface TryOnResponse {
  url: string;
}

export async function generateTryOn(bodyImageUrl: string, clothingItems: TryOnItem[]): Promise<TryOnResponse> {
  return apiPost<TryOnResponse>("/api/tryon/generate", {
    body_image_url: bodyImageUrl,
    clothing_items: clothingItems,
  });
}
