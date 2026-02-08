export interface ShippingInfo {
  fullName?: string;
  email?: string;
  address?: string;
  city?: string;
  zip?: string;
}

export interface CheckoutItem {
  productId: string;
  quantity: number;
}

export interface CheckoutRequest {
  items: CheckoutItem[];
  shipping?: ShippingInfo;
}

export interface CheckoutResponse {
  orderId: string;
  status: string;
  total: number;
  savings: number;
  lineItems: { productId: string; name: string; retailer: string; quantity: number; price: number; subtotal: number }[];
  shipping: ShippingInfo;
  message: string;
}
