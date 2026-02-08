import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from zep_cloud.types import Message

from .client import add_message_to_thread, get_zep_client

logger = logging.getLogger(__name__)


def update_user_persona_with_outfit_summaries(
    user_id: str,
    summaries: List[Dict[str, Any]],
    pinterest_boards: Optional[List[Dict[str, Any]]] = None,
    colors: Optional[List[str]] = None,
    styles: Optional[List[str]] = None,
    user_email: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> bool:
    """
    Store outfit summaries as messages to the user's thread.

    Design intent:
    - Persona memory is driven by messages; Zep ingests them automatically into the per-user graph.
    - No manual graph entities or edges are created here to avoid duplicating message content.
    """
    client = get_zep_client()
    if not client:
        logger.error("[Zep] Client not initialized. Cannot store summaries.")
        return False
    if not thread_id:
        logger.error("[Zep] thread_id is required to store summaries.")
        return False

    try:
        added = 0
        for s in summaries:
            logger.info("[Zep] Storing summary for user %s", user_id)
            result = add_outfit_summary_to_graph(
                user_id=user_id,
                summary=s.get("summary_data", {}),
                image_url=s.get("image_url"),
                timestamp=s.get("timestamp"),
                user_email=user_email,
                thread_id=thread_id,
            )
            if result:
                added += 1

        logger.info("[Zep] Added %s/%s summaries to thread %s", added, len(summaries), thread_id)
        return added > 0
    except Exception as exc:
        logger.exception("[Zep] Failed to store outfit summaries: %s", exc)
        return False


def add_outfit_summary_to_graph(
    user_id: str,
    summary: Dict[str, Any],
    image_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    user_email: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> Optional[bool]:
    """
    Store a single outfit summary as a message to the user's thread.
    """
    client = get_zep_client()
    if not client or not thread_id:
        logger.error("[Zep] Missing client or thread_id. user=%s thread=%s", user_id, thread_id)
        return None

    try:
        nl_summary = summary.get("summary") or "Outfit summary not provided"
        items = ", ".join(summary.get("items", [])) or "items not specified"
        colors = ", ".join(summary.get("colors", [])) or "colors not specified"
        styles = ", ".join(summary.get("style_keywords", [])) or "style not specified"
        fit = summary.get("fit") or "fit not specified"
        occasion = summary.get("occasion") or "occasion not specified"

        content = (
            f"Outfit observed from Pinterest. "
            f"Summary: {nl_summary}. Items: {items}. Colors: {colors}. "
            f"Style: {styles}. Fit: {fit}. Occasion: {occasion}. "
            f"Image URL: {image_url or 'n/a'}. Timestamp: {timestamp or 'n/a'}."
        )

        payload = {
            "user_id": str(user_id),
            "user_email": user_email,
            "image_url": image_url,
            "summary": summary.get("summary"),
            "items": summary.get("items", []),
            "colors": summary.get("colors", []),
            "style_keywords": summary.get("style_keywords", []),
            "fit": summary.get("fit"),
            "occasion": summary.get("occasion"),
            "source": "pinterest",
            "timestamp": timestamp,
        }
        _ = json.dumps(payload)

        created_at = _normalize_timestamp(timestamp)
        message = Message(
            created_at=created_at,
            name=f"Pinterest user {user_id}",
            role="user",
            content=content,
            metadata={
                "source": "pinterest_outfit_summary",
                "user_id": str(user_id),
                "user_email": str(user_email) if user_email else "",
            },
        )

        logger.debug("[Zep] Sending message content: %s", content)
        add_message_to_thread(client, thread_id=thread_id, message=message)
        return True
    except Exception as exc:
        logger.exception("[Zep] Failed to add outfit summary: %s", exc)
        return None


def _normalize_timestamp(value: Optional[str]) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()

    text = str(value).strip()
    if text.isdigit():
        return datetime.fromtimestamp(float(text), tz=timezone.utc).isoformat()

    if text.endswith("Z"):
        text = text.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
