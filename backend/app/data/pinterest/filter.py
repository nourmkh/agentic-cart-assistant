"""
Outfit/Fashion Image Filtering Service using Groq LLM.
Filters Pinterest pins to only include outfit/clothing/fashion-related images.
"""

import logging
import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

try:
    from groq import Groq

    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("✓ Groq client initialized successfully")
    else:
        groq_client = None
        logger.warning("✗ GROQ_API_KEY not set. Outfit filtering disabled.")
except Exception:
    groq_client = None
    logger.warning("✗ Groq package not installed. Outfit filtering disabled.")


def is_outfit_or_fashion(image_url: str, pin_description: str = "") -> Optional[bool]:
    if not groq_client:
        logger.warning("[Filter] Groq client not initialized")
        return None
    if not image_url:
        logger.debug("[Filter] Missing image URL")
        return False

    try:
        prompt_text = (
            "Based ONLY on the IMAGE content (ignore any text), is this showing an outfit, "
            "clothing item, fashion styling, or wearable fashion inspiration? Answer ONLY 'YES' or 'NO'."
        )

        logger.debug("[Filter] Calling Groq VLM for outfit check")
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=10,
            top_p=0.1,
            stream=False,
        )

        response_text = completion.choices[0].message.content.strip().upper()
        logger.debug("[Filter] Raw response: %s", response_text)
        response_clean = response_text.strip().upper().rstrip('.,!?;:\'" ')

        if "YES" in response_clean:
            return True
        if "NO" in response_clean:
            return False
        return False
    except Exception:
        logger.exception("[Filter] Failed to analyze image")
        return None


def filter_pinterest_pins(pins: list, descriptions: Dict[str, str] = None, max_pins: int = 50) -> Dict[str, Any]:
    descriptions = descriptions or {}

    original_count = len(pins)
    if len(pins) > max_pins:
        logger.warning("[Filter] Pin count %s exceeds max %s. Trimming.", len(pins), max_pins)
        pins = pins[:max_pins]

    accepted = []
    rejected = []
    failed = []

    logger.info("[Filter] Filtering %s pins", len(pins))
    for pin in pins:
        pin_id = pin.get("id")
        image_url = pin.get("image_url")
        description = descriptions.get(pin_id, pin.get("description", ""))

        logger.debug("[Filter] Pin %s image=%s", pin_id, bool(image_url))
        result = is_outfit_or_fashion(image_url, description)
        if result is True:
            accepted.append(pin)
        elif result is False:
            rejected.append(pin)
        else:
            failed.append(pin)

    stats = {
        "total": len(pins),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "failed": len(failed),
        "acceptance_rate": f"{(len(accepted) / len(pins) * 100):.1f}%" if pins else "0%",
        "original_count": original_count,
    }

    logger.info("[Filter] Stats: %s", stats)

    return {
        "accepted": accepted,
        "rejected": rejected,
        "failed": failed,
        "stats": stats,
    }


def summarize_outfit(image_url: str) -> Optional[dict]:
    if not groq_client:
        logger.warning("[Filter] Groq client not initialized (summarize)")
        return None
    if not image_url:
        logger.debug("[Filter] Missing image URL for summarize")
        return None

    try:
        prompt = (
            "Analyze ONLY the IMAGE content and return a STRICT JSON object (no prose) with keys: "
            "summary (string), items (array of strings), colors (array of strings), "
            "style_keywords (array of strings), fit (string or null), occasion (string or null). "
            "Focus on wearable outfit components; if the image is not fashion, return an empty JSON object {}."
        )

        logger.debug("[Filter] Calling Groq VLM for outfit summary")
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            temperature=0.1,
            max_completion_tokens=256,
            top_p=0.1,
            stream=False,
        )

        text = completion.choices[0].message.content.strip()
        logger.debug("[Filter] Raw summary response length=%s", len(text))
        if text.startswith("```"):
            text = text.lstrip("`").lstrip("json").lstrip("`").strip()
        if text.endswith("```"):
            text = text.rstrip("`").strip()

        import json

        data = json.loads(text)
        if not isinstance(data, dict) or not data.get("summary"):
            return None

        for k in ["items", "colors", "style_keywords"]:
            v = data.get(k)
            if isinstance(v, list):
                data[k] = [str(x).strip() for x in v if str(x).strip()]
            else:
                data[k] = []

        data["fit"] = data.get("fit") or None
        data["occasion"] = data.get("occasion") or None

        logger.debug("[Filter] Parsed summary: %s", data)
        return data
    except Exception:
        logger.exception("[Filter] Failed to summarize outfit")
        return None
