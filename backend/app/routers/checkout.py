import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/api/checkout", tags=["checkout"])
automation_service = AutomationService()

class CheckoutItem(BaseModel):
    id: str
    title: str
    retailer: str = ""
    link: str = ""
    price: float = 0.0
    variant: Optional[Dict[str, Any]] = None
    color: Optional[str] = None
    size: Optional[str] = None

class UserData(BaseModel):
    name: str = ""
    email: str = ""
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
        thread = threading.Thread(
            target=automation_service.run_checkout,
            args=([item.dict() for item in request.items], request.user_data.dict()),
            daemon=True
        )
        thread.start()
        
        return {"status": "success", "message": "Personal Shopper agent started in a new window."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
