import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.data.agent import get_agent_logs
from app.data.llm_extractor.extractor import extract_user_requirements
from app.data.search_cache import set_last_search
from app.schemas.agent import SearchRequest, SearchResultItem
from app.services.RetailProduct import search_products
from app.services.RetailProduct.search import _serper_search, _serper_shopping, _tavily_search

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _infer_item_from_prompt(prompt: str) -> str:
    text = prompt.lower()
    keywords = [
        "t-shirt",
        "tshirt",
        "tee",
        "shirt",
        "pants",
        "jeans",
        "shorts",
        "hoodie",
        "sweater",
        "jacket",
        "dress",
        "skirt",
        "shoes",
        "sneakers",
        "boots",
        "bag",
    ]
    for k in keywords:
        if k in text:
            return "t-shirt" if k in {"tshirt", "tee"} else k
    return ""


def _clean_item_text(item: str, colors: list[str], style_list: list[str], target: str) -> str:
    text = item.lower()
    for t in [target, "women", "women's", "men", "men's", "kids", "kid", "girl", "boy"]:
        if t:
            text = re.sub(rf"\b{re.escape(t)}\b", "", text)
    for c in colors:
        text = re.sub(rf"\b{re.escape(c.lower())}\b", "", text)
    for s in style_list:
        text = re.sub(rf"\b{re.escape(s.lower())}\b", "", text)
    text = re.sub(r"\bunder\b|\bby\b|\bin\b|\bwithin\b", "", text)
    text = re.sub(r"\$\s*\d+(?:\.\d+)?|\d+\s*\$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@router.get("/logs")
def agent_logs():
    return get_agent_logs()


@router.get("/serper-test")
async def serper_test():
    """
    Debug: test Serper API with a single shopping query.
    Returns whether the key is set, and the raw Serper response or error.
    """
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return {"key_set": False, "error": "SERPER_API_KEY not set in env", "raw": None}
    try:
        raw = await _serper_shopping("casual shirt", api_key, num=3)
        return {
            "key_set": True,
            "status": "ok",
            "results_count": len(raw),
            "raw_sample": raw[:2] if raw else [],
        }
    except Exception as e:
        return {
            "key_set": True,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/serper-search-test")
async def serper_search_test(q: str = "blue t-shirt women"):
    """Debug: test Serper search endpoint with a query."""
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return {"key_set": False, "error": "SERPER_API_KEY not set in env", "raw": None}
    try:
        raw = await _serper_search(q, api_key, num=5)
        return {
            "key_set": True,
            "status": "ok",
            "results_count": len(raw),
            "raw_sample": raw[:2] if raw else [],
        }
    except Exception as e:
        return {
            "key_set": True,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/tavily-test")
async def tavily_test(q: str = "blue t-shirt women"):
    """Debug: test Tavily search endpoint with a query."""
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {"key_set": False, "error": "TAVILY_API_KEY not set in env", "raw": None}
    try:
        raw = await _tavily_search(q, api_key, num=5)
        return {
            "key_set": True,
            "status": "ok",
            "results_count": len(raw),
            "raw_sample": raw[:2] if raw else [],
        }
    except Exception as e:
        return {
            "key_set": True,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.post("/search", response_class=JSONResponse)
async def agent_search(request: SearchRequest):
    """
    Intelligent shopping agent: search for products matching budget, deadline,
    size, and style. Returns structured JSON: query echo, results grouped by item, totals.
    """
    if request.prompt:
        extracted = extract_user_requirements(request.prompt, request.preferences)
        style_list = extracted.get("style") or []
        colors = extracted.get("colors") or []
        item = (extracted.get("item") or "").strip()
        constraints = " ".join(extracted.get("constraints") or []).lower()
        target = (extracted.get("target") or "").strip().lower()
        if not target:
            for t in ["women", "men", "kids", "women's", "men's", "girl", "boy"]:
                if t in constraints or t in request.prompt.lower():
                    target = "women" if "women" in t or "girl" in t else "men" if "men" in t or "boy" in t else "kids"
                    break

        budget = extracted.get("budget") or request.budget
        deadline = extracted.get("deadline") or request.deadline
        style = " ".join(style_list) if style_list else request.style
        color = colors[0] if colors else request.color
        size = (extracted.get("size") or request.size).strip()

        cleaned_item = _clean_item_text(item, colors, style_list, target)
        inferred = _infer_item_from_prompt(request.prompt)
        final_item = inferred or cleaned_item or item
        items = [final_item] if final_item else request.items
    else:
        budget = request.budget
        deadline = request.deadline
        style = request.style
        color = request.color
        items = request.items
        size = request.size
        target = request.target

    results, _debug = await search_products(
        budget=budget,
        deadline=deadline,
        size=size,
        style=style,
        target=target,
        color=color,
        items=items,
    )
    # Build structured response: query, results_by_item, total_count, retailers
    query_echo = {
        "budget": budget,
        "deadline": deadline,
        "size": size,
        "style": style,
        "target": target,
        "color": color,
        "items": items,
    }
    results_by_item: dict[str, list] = {}
    retailers_set: set[str] = set()
    for r in results:
        item_key = r.item or "other"
        if item_key not in results_by_item:
            results_by_item[item_key] = []
        results_by_item[item_key].append(r.model_dump())
        retailers_set.add(r.retailer)
    payload = {
        "query": query_echo,
        "results_by_item": results_by_item,
        "total_count": len(results),
        "retailers": sorted(retailers_set),
    }
    set_last_search(payload)
    set_last_search(payload)
    # Pretty-print JSON (indent=2) for easier reading
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
    )
