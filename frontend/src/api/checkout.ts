import { apiPost } from "./client";

export interface AutomateCheckoutRequest {
    items: {
        id: string;
        name: string;
        retailer: string;
        url: string;
        price: number;
        size: string;
    }[];
    user_data: {
        name: string;
        email: string;
        address?: string;
        city?: string;
        zip?: string;
    };
}

export async function automateCheckout(data: AutomateCheckoutRequest): Promise<{ status: string; message: string }> {
    return apiPost<{ status: string; message: string }>("/api/checkout/automate", data);
}
