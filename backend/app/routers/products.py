from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.data.products import get_products
from app.ranking import process_and_rank, get_weights

router = APIRouter(prefix="/api/products", tags=["products"])


class SearchRequest(BaseModel):
    query: str
    preferences: List[str] = []
    budget: Optional[float] = 400.0
    max_delivery_days: Optional[float] = 5.0


@router.get("")
def list_products():
    return get_products()


@router.post("/search")
def search_products(request: SearchRequest):
    """
    Search and rank products based on query and user preferences.
    
    Preferences mapping:
    - "Budget" -> increases price weight
    - "Fast Delivery" -> increases delivery weight  
    - "My Style" -> increases style weight
    """
    # Get all products (in a real app, this would search/filter products)
    all_products = get_products()
    
    # Convert products to format expected by ranking engine
    # Add delivery_days field if missing (parse from delivery string)
    def parse_delivery_days(delivery_str: str) -> float:
        """Parse delivery string to days"""
        if isinstance(delivery_str, (int, float)):
            return float(delivery_str)
        if not isinstance(delivery_str, str):
            return 5.0
        import re
        numbers = re.findall(r'\d+', delivery_str.lower())
        if numbers:
            return float(numbers[0])
        if "tomorrow" in delivery_str.lower():
            return 1.0
        return 5.0
    
    # Group products by category for ranking
    products_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for product in all_products:
        category = product.get("category", "Other")
        if category not in products_by_category:
            products_by_category[category] = []
        
        # Ensure product has required fields for ranking
        product_copy = product.copy()
        if "delivery_days" not in product_copy:
            delivery_str = product_copy.get("delivery", "5 days")
            product_copy["delivery_days"] = parse_delivery_days(delivery_str)
        if "preference_match" not in product_copy:
            product_copy["preference_match"] = 0.8  # Default match score
        
        products_by_category[category].append(product_copy)
    
    # Prepare client data with preferences
    client_data = {
        "budget": request.budget,
        "delivery_deadline": request.max_delivery_days,
        "preferences_clicked": request.preferences,
        "query": request.query
    }
    
    # Default persona (can be enhanced later)
    zep_persona = {
        "preferred_styles": ["minimaliste", "sporty"],
        "preferred_colors": ["blue", "black"]
    }
    
    # Process and rank products
    # Note: process_and_rank expects products_data with "items" key containing products_by_category
    products_data = {
        "query": request.query,
        "items": products_by_category
    }
    ranked_results = process_and_rank(products_data, client_data, zep_persona)
    
    # Get weights for response
    weights = get_weights(request.preferences)
    
    # Format response for frontend
    formatted_results = {}
    for category, ranked_items in ranked_results.items():
        formatted_results[category] = {
            "category": category,
            "weights": weights,
            "products": [
                {
                    "rank": idx + 1,
                    "product": item["product"],
                    "score": item["score"],
                    "score_breakdown": item["decomposition"],
                    "explanation": item.get("why_local", ""),
                    "llm_explanation": item.get("llm_explanation", "")
                }
                for idx, item in enumerate(ranked_items)
            ]
        }
    
    return {
        "query": request.query,
        "preferences": request.preferences,
        "weights": weights,
        "results": formatted_results
    }


@router.get("/{product_id}")
def get_product(product_id: str):
    products = get_products()
    for p in products:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")
