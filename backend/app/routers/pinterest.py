import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data.pinterest import PinterestOAuthService, get_connection_status, set_connected

router = APIRouter(prefix="/api/pinterest", tags=["pinterest"])


@router.get("/login")
def pinterest_login():
    """Return Pinterest OAuth URL for the frontend to redirect."""
    state = secrets.token_urlsafe(32)
    oauth_url = PinterestOAuthService.get_oauth_url(state)
    return {"oauth_url": oauth_url, "state": state}


@router.get("/status")
def pinterest_status():
    """Return whether Pinterest is connected (in-memory)."""
    return get_connection_status()


@router.get("/callback")
def pinterest_callback(code: Optional[str] = None, state: Optional[str] = None):
    """Mark Pinterest as connected after OAuth callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    set_connected()
    return {"success": True}
