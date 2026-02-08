import secrets
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel

from app.data.pinterest import (
    PinterestOAuthService,
    get_connection_status,
    set_connected,
    set_access_token,
    set_profile,
    set_zep_user,
    set_zep_thread,
    get_zep_user_id,
    get_zep_thread_id,
)
from app.data.pinterest.sync import sync_pinterest_to_zep
from app.data.ZEP_mcp import update_user_persona_with_outfit_summaries
from app.data.ZEP_mcp import get_zep_client, ensure_zep_user, ensure_zep_thread

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
def pinterest_callback(code: Optional[str] = None, state: Optional[str] = None, user_email: Optional[str] = None):
    """Exchange code, fetch Pinterest profile, and create Zep user/thread."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_data = PinterestOAuthService.exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

    try:
        profile = PinterestOAuthService.fetch_user_profile(access_token)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=400,
                detail="Pinterest authorization failed. Reconnect and allow user_accounts:read scope.",
            )
        raise
    set_access_token(access_token)
    set_profile(profile)

    pinterest_user_id = profile.get("id") or profile.get("username") or "pinterest-user"
    pinterest_name = profile.get("username") or "Pinterest User"
    name_parts = pinterest_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    client = get_zep_client()
    if not client:
        raise HTTPException(status_code=500, detail="ZEP_API_KEY not configured")

    ensure_zep_user(client, user_id=str(pinterest_user_id), email=user_email, first_name=first_name, last_name=last_name)
    thread_id = ensure_zep_thread(client, user_id=str(pinterest_user_id), thread_id=f"pinterest-{pinterest_user_id}")

    set_zep_user(str(pinterest_user_id))
    set_zep_thread(thread_id)
    set_connected()

    sync_result = sync_pinterest_to_zep(
        user_id=str(pinterest_user_id),
        access_token=access_token,
        thread_id=thread_id,
        user_email=user_email,
    )

    return {
        "success": True,
        "user_id": str(pinterest_user_id),
        "thread_id": thread_id,
        "boards_count": sync_result.get("boards_count", 0),
        "pins_count": sync_result.get("pins_count", 0),
    }


class PinterestSyncPayload(BaseModel):
    summaries: List[Dict[str, Any]]
    pinterest_boards: Optional[List[Dict[str, Any]]] = None
    colors: Optional[List[str]] = None
    styles: Optional[List[str]] = None
    user_email: Optional[str] = None


@router.post("/sync")
def pinterest_sync(payload: PinterestSyncPayload):
    """Sync Pinterest summaries to Zep graph via thread messages."""
    user_id = get_zep_user_id()
    thread_id = get_zep_thread_id()
    if not user_id or not thread_id:
        raise HTTPException(status_code=400, detail="Pinterest is not connected")

    success = update_user_persona_with_outfit_summaries(
        user_id=user_id,
        summaries=payload.summaries,
        pinterest_boards=payload.pinterest_boards,
        colors=payload.colors,
        styles=payload.styles,
        user_email=payload.user_email,
        thread_id=thread_id,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync Pinterest data to Zep")

    return {"success": True}
