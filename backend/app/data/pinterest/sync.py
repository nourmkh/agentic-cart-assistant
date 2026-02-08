from typing import Any, Dict, List, Optional

from app.data.ZEP_mcp import update_user_persona_with_outfit_summaries
from app.data.pinterest.api import PinterestAPIService, extract_pin_image_url
from app.data.pinterest.filter import filter_pinterest_pins, summarize_outfit
import logging

logger = logging.getLogger(__name__)


def sync_pinterest_to_zep(
    user_id: str,
    access_token: str,
    thread_id: str,
    user_email: Optional[str] = None,
    pins_per_board: int = 10,
) -> Dict[str, Any]:
    api = PinterestAPIService(access_token)

    boards = api.get_boards()
    logger.info("[Pinterest Sync] Boards fetched: %s", len(boards))
    all_pins: List[Dict[str, Any]] = []

    for board in boards:
        board_id = board.get("id")
        if not board_id:
            continue
        pins = api.get_board_pins(board_id, limit=pins_per_board)
        logger.info("[Pinterest Sync] Board %s pins: %s", board.get("name"), len(pins))
        for pin in pins:
            pin["board_name"] = board.get("name")
        all_pins.extend(pins)

    pins_with_images: List[Dict[str, Any]] = []
    for pin in all_pins:
        image_url = extract_pin_image_url(pin)
        if image_url:
            pin["image_url"] = image_url
            pins_with_images.append(pin)
        logger.debug("[Pinterest Sync] Pin %s image=%s desc=%s", pin.get("id"), bool(image_url), pin.get("description"))

    filter_result = filter_pinterest_pins(pins_with_images)
    filtered_pins = filter_result.get("accepted", [])
    logger.info("[Pinterest Sync] Filtered pins: %s", len(filtered_pins))

    summaries: List[Dict[str, Any]] = []
    for pin in filtered_pins:
        image_url = pin.get("image_url")
        summary_data = summarize_outfit(image_url) if image_url else None
        if not summary_data:
            description = pin.get("description") or ""
            title = pin.get("title") or ""
            summary_text = title or description or "Pinterest pin"
            summary_data = {
                "summary": summary_text,
                "items": [],
                "colors": [],
                "style_keywords": [],
                "fit": None,
                "occasion": None,
            }

        summaries.append(
            {
                "image_url": image_url,
                "summary_data": summary_data,
                "timestamp": pin.get("created_at"),
            }
        )
        logger.debug("[Pinterest Sync] Summary for pin %s: %s", pin.get("id"), summary_data)

    success = update_user_persona_with_outfit_summaries(
        user_id=user_id,
        summaries=summaries,
        pinterest_boards=[{"name": b.get("name"), "description": b.get("description")} for b in boards],
        colors=None,
        styles=None,
        user_email=user_email,
        thread_id=thread_id,
    )

    return {
        "success": bool(success),
        "boards_count": len(boards),
        "pins_count": len(filtered_pins),
    }
