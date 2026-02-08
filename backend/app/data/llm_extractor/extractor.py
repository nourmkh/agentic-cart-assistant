import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from groq import Groq


MODEL_NAME = "openai/gpt-oss-120b"

logger = logging.getLogger(__name__)


def _get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def extract_user_requirements(user_prompt: str, preferences: Optional[List[str]] = None) -> Dict[str, Any]:
    client = _get_client()
    preferences = preferences or []

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict information extractor. Return ONLY valid JSON. "
                        "Schema: {budget:string, style:[string], deadline:string, colors:[string], "
                        "item:string, constraints:[string]}. "
                        "Infer budget/deadline if present. Infer style keywords and colors. "
                        "Use empty string/array when missing."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User input: {user_prompt}\n"
                        f"Preferences tickets: {', '.join(preferences) if preferences else 'none'}"
                    ),
                },
            ],
            max_completion_tokens=300,
            temperature=0,
            top_p=1,
        )
    except Exception as exc:
        logger.exception("[LLM Extract] Groq call failed: %s", exc)
        raise

    message = response.choices[0].message
    content = message.content or "{}"
    try:
        data = json.loads(content)
    except Exception:
        data = {}

    data = _normalize_data(data, user_prompt, preferences)
    logger.info("[LLM Extract] %s", data)
    return data


def _normalize_data(data: Dict[str, Any], user_prompt: str, preferences: List[str]) -> Dict[str, Any]:
    normalized = {
        "budget": str(data.get("budget") or ""),
        "style": data.get("style") or [],
        "deadline": str(data.get("deadline") or ""),
        "colors": data.get("colors") or [],
        "item": str(data.get("item") or ""),
        "constraints": data.get("constraints") or [],
    }

    if not normalized["item"]:
        normalized["item"] = user_prompt.strip()

    fallback = _fallback_extract(user_prompt)
    for key in ["budget", "deadline"]:
        if not normalized[key] and fallback.get(key):
            normalized[key] = fallback[key]

    if not normalized["colors"] and fallback.get("colors"):
        normalized["colors"] = fallback["colors"]

    if not normalized["style"] and fallback.get("style"):
        normalized["style"] = fallback["style"]

    if preferences:
        normalized["constraints"] = list({*normalized["constraints"], *preferences})

    return normalized


def _fallback_extract(text: str) -> Dict[str, Any]:
    lower = text.lower()

    budget = ""
    dollar_match = re.search(r"\$\s*(\d+(?:\.\d+)?)", text)
    if dollar_match:
        budget = f"${dollar_match.group(1)}"
    else:
        budget_match = re.search(r"budget\s*(?:of|:)?\s*(\d+(?:\.\d+)?)", lower)
        if budget_match:
            budget = f"${budget_match.group(1)}"

    deadline = ""
    deadline_match = re.search(r"\bby\s+([a-zA-Z]+)\b", lower)
    if deadline_match:
        deadline = f"by {deadline_match.group(1)}"

    color_list = [
        "white",
        "black",
        "gray",
        "grey",
        "red",
        "blue",
        "green",
        "yellow",
        "pink",
        "purple",
        "orange",
        "brown",
        "beige",
    ]
    colors = [c for c in color_list if re.search(rf"\b{re.escape(c)}\b", lower)]

    style_keywords = ["sporty", "sport", "chic", "trendy", "casual", "formal", "streetwear"]
    styles = [s for s in style_keywords if re.search(rf"\b{re.escape(s)}\b", lower)]

    return {
        "budget": budget,
        "deadline": deadline,
        "colors": colors,
        "style": styles,
    }
