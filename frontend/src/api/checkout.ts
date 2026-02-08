import { apiPost } from "./client";

export interface AutomateCheckoutRequest {
    items: {
        id: string;
        title: string;
        retailer: string;
        link: string;
        price: number;
        variant?: {
            size?: string;
            color?: string;
            material?: string;
        };
        size?: string;
        color?: string;
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
