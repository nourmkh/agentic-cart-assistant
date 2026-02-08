import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/api/checkout", tags=["checkout"])
automation_service = AutomationService()

class CartVariant(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None


class CheckoutItem(BaseModel):
    # Accept both cart schema and legacy checkout schema
    id: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None
    retailer: Optional[str] = None
    link: Optional[str] = None
    url: Optional[str] = None
    price: float
    currency: Optional[str] = None
    image: Optional[str] = None
    deliveryEstimate: Optional[str] = None
    shortDescription: Optional[str] = None
    variant: Optional[CartVariant] = None
    verified: Optional[bool] = None
    size: Optional[str] = None
    color: Optional[str] = None

class UserData(BaseModel):
    name: str
    email: str
    address: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None

class AutomateRequest(BaseModel):
    items: List[CheckoutItem]
    user_data: UserData

@router.post("/automate")
async def automate_checkout(request: AutomateRequest):
    """
    Endpoint to trigger automated checkout via Playwright.
    Runs in a dedicated thread to avoid asyncio loop issues on Windows.
    """
    try:
        # Create a thread to run the synchronous automation
        normalized_items = []
        for item in request.items:
            name = item.name or item.title or ""
            url = item.url or item.link or ""
            size = item.size or (item.variant.size if item.variant else None) or ""
            color = item.color or (item.variant.color if item.variant else None)
            normalized_items.append(
                {
                    "id": item.id or "",
                    "name": name,
                    "retailer": item.retailer or "",
                    "url": url,
                    "price": item.price,
                    "size": size,
                    "color": color,
                }
            )

        thread = threading.Thread(
            target=automation_service.run_checkout,
            args=(normalized_items, request.user_data.dict()),
            daemon=True
        )
        thread.start()
        
        return {
            "status": "success",
            "message": "Personal Shopper agent started in a new window.",
            "items": normalized_items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
