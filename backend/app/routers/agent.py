import json
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.data.agent import get_agent_logs
from app.data.search_cache import set_last_search
from app.data.search_cache import set_last_search
from app.schemas.agent import SearchRequest, SearchResultItem
from app.services.RetailProduct import search_products
from app.services.RetailProduct.search import _serper_search, _serper_shopping, _tavily_search

router = APIRouter(prefix="/api/agent", tags=["agent"])


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
    results, _debug = await search_products(
        budget=request.budget,
        deadline=request.deadline,
        size=request.size,
        style=request.style,
        target=request.target,
        color=request.color,
        items=request.items,
    )
    # Build structured response: query, results_by_item, total_count, retailers
    query_echo = {
        "budget": request.budget,
        "deadline": request.deadline,
        "size": request.size,
        "style": request.style,
        "target": request.target,
        "color": request.color,
        "items": request.items,
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
