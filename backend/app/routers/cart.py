import json
import re
from typing import Any
from pathlib import Path

import logging
from fastapi import APIRouter

from app.data.search_cache import get_last_extract, get_last_search, set_last_search
from app.schemas.agent import SearchItem
from app.services.RetailProduct import search_products
from app.services.ranking_service import process_from_extract_and_results

router = APIRouter(prefix="/api/cart", tags=["cart"])
logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _infer_item_from_text(text: str) -> str:
    lowered = text.lower()
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
    for keyword in keywords:
        if keyword in lowered:
            return "t-shirt" if keyword in {"tshirt", "tee"} else keyword
    return ""


def _infer_items_from_text(text: str) -> list[str]:
    lowered = text.lower()
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
    items: list[str] = []
    for keyword in keywords:
        if keyword in lowered:
            normalized = "t-shirt" if keyword in {"tshirt", "tee"} else keyword
            if normalized == "shirt" and "t-shirt" in items:
                continue
            if normalized not in items:
                items.append(normalized)
    return items


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


def _extract_signature(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def _to_ranking_item(result: Any) -> dict:
    if isinstance(result, dict):
        return {
            "name": result.get("name") or result.get("title") or "",
            "price": float(result.get("price") or 0.0),
            "delivery_estimate": result.get("delivery_estimate") or result.get("deliveryEstimate") or result.get("delivery") or "",
            "retailer": result.get("retailer") or "",
            "item": result.get("item") or "",
        }
    return {
        "name": getattr(result, "name", ""),
        "price": float(getattr(result, "price", 0.0)),
        "delivery_estimate": getattr(result, "delivery_estimate", ""),
        "retailer": getattr(result, "retailer", ""),
        "item": getattr(result, "item", ""),
    }


def _load_default_payload() -> dict:
    defaults = {
        "budget": "$70",
        "deadline": "30 days",
        "size": "M",
        "style": "casual",
        "target": "women",
        "color": "",
        "items": ["t-shirt"],
    }
    try:
        base_dir = Path(__file__).resolve().parents[3]
        payload_path = base_dir / "test-search.json"
        if payload_path.exists():
            raw = json.loads(payload_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                defaults.update(raw)
    except Exception:
        pass
    return defaults


@router.get("")
async def get_cart(
    budget: str | None = None,
    deadline: str | None = None,
    size: str | None = None,
    style: str | None = None,
    target: str | None = None,
    color: str | None = None,
    items: str | None = None,
):
    has_query_params = any([budget, deadline, size, style, target, color, items])
    last_extract = get_last_extract()
    last = get_last_search()
    if not has_query_params and last_extract:
        extract_signature = _extract_signature(last_extract)
        if last and last.get("source") == "llm-extract" and last.get("extract_signature") == extract_signature:
            results_by_item = last.get("results_by_item") or {}
            results = []
            for item_key, items_list in results_by_item.items():
                for r in items_list:
                    r["item"] = item_key
                    results.append(r)
        else:
            defaults = _load_default_payload()
            data = last_extract.get("data") or {}
            prompt_text = str(last_extract.get("query") or "").strip()
            style_list = data.get("style") or []
            colors = data.get("colors") or []
            item_text = str(data.get("item") or "").strip()
            constraints = " ".join(data.get("constraints") or []).lower()
            target = str(data.get("target") or "").strip().lower()
            if not target:
                prompt_lower = f"{prompt_text} {item_text}".lower()
                for t in ["women", "men", "kids", "women's", "men's", "girl", "boy"]:
                    if t in constraints or t in prompt_lower:
                        target = "women" if "women" in t or "girl" in t else "men" if "men" in t or "boy" in t else "kids"
                        break
            budget = data.get("budget") or defaults["budget"]
            deadline = data.get("deadline") or defaults["deadline"]
            size = str(data.get("size") or defaults["size"]).strip()
            style = " ".join(style_list) if style_list else defaults["style"]
            color = colors[0] if colors else defaults["color"]

            inferred_items = _infer_items_from_text(item_text or prompt_text)
            if len(colors) > 1 and len(inferred_items) > 1:
                color = ""

            cleaned_item = _clean_item_text(item_text or prompt_text, colors, style_list, target)
            inferred = _infer_item_from_text(prompt_text or item_text)
            final_item = inferred or cleaned_item or item_text or prompt_text

            if inferred_items:
                item_specs = [
                    SearchItem(name=name, color=colors[idx] if idx < len(colors) else "", size=size)
                    for idx, name in enumerate(inferred_items)
                ]
            elif final_item:
                item_specs = [SearchItem(name=final_item, color=color, size=size)]
            else:
                item_specs = [SearchItem(name=name, color=color, size=size) for name in defaults["items"]]

            results, _debug = await search_products(
                budget=budget,
                deadline=deadline,
                size=size,
                style=style,
                target=target or defaults["target"],
                color=color,
                items=item_specs,
            )

            results_by_item: dict[str, list] = {}
            retailers_set: set[str] = set()
            for r in results:
                item_key = r.item or "other"
                results_by_item.setdefault(item_key, []).append(r.model_dump())
                retailers_set.add(r.retailer)

            set_last_search(
                {
                    "source": "llm-extract",
                    "extract_signature": extract_signature,
                    "query": {
                        "budget": budget,
                        "deadline": deadline,
                        "size": size,
                        "style": style,
                        "target": target or defaults["target"],
                        "color": color,
                        "items": [spec.model_dump() for spec in item_specs],
                    },
                    "results_by_item": results_by_item,
                    "total_count": len(results),
                    "retailers": sorted(retailers_set),
                }
            )
    elif last and not has_query_params:
        results_by_item = last.get("results_by_item") or {}
        results = []
        for item_key, items_list in results_by_item.items():
            for r in items_list:
                r["item"] = item_key
                results.append(r)
    else:
        defaults = _load_default_payload()
        budget = budget or defaults["budget"]
        deadline = deadline or defaults["deadline"]
        size = size or defaults["size"]
        style = style or defaults["style"]
        target = target or defaults["target"]
        color = color if color is not None else defaults["color"]
        item_list = defaults["items"]
        if items is not None:
            item_list = [i.strip() for i in items.split(",") if i.strip()]
        item_specs = [SearchItem(name=name, color=color, size=size) for name in item_list]
        results, _debug = await search_products(
            budget=budget,
            deadline=deadline,
            size=size,
            style=style,
            target=target,
            color=color,
            items=item_specs,
        )

    last_extract = get_last_extract() or {}
    ranking_lookup: dict[tuple[str, str], dict] = {}
    if last_extract and results:
        try:
            extract_data = last_extract.get("data") or {}
            ranking_results = [_to_ranking_item(r) for r in results]
            logger.info("[RankingWorkflow] running from cart results (%s items)", len(ranking_results))
            ranking_payload = process_from_extract_and_results(extract_data, ranking_results)
            ranked_by_category = ranking_payload.get("results") or {}
            for _category, ranked_items in ranked_by_category.items():
                # ranked_items is a list of {product, score, decomposition, why_local, llm_explanation?}
                for idx, entry in enumerate(ranked_items, start=1):
                    product = entry.get("product") or {}
                    key = (str(product.get("name") or ""), str(product.get("retailer") or ""))
                    if not key[0]:
                        continue
                    ranking_lookup[key] = {
                        "rank": idx,
                        "score": entry.get("score"),
                        "llm_explanation": entry.get("llm_explanation") if idx == 1 else "",
                        "why_local": entry.get("why_local") or "",
                    }
        except Exception as exc:
            logger.exception("[RankingWorkflow] failed: %s", exc)

    cart_items = []
    for idx, r in enumerate(results):
        variants = r.get("variants") if isinstance(r, dict) else r.variants
        sizes = variants.get("sizes") if isinstance(variants, dict) else variants.sizes
        colors = variants.get("colors") if isinstance(variants, dict) else variants.colors
        material = variants.get("material") if isinstance(variants, dict) else variants.material
        size_value = sizes[0] if sizes else ""
        color_value = colors[0] if colors else ""
        material_value = material[0] if material else ""
        name = r.get("name") if isinstance(r, dict) else r.name
        price = r.get("price") if isinstance(r, dict) else r.price
        image_url = r.get("image_url") if isinstance(r, dict) else r.image_url
        retailer = r.get("retailer") if isinstance(r, dict) else r.retailer
        delivery_estimate = r.get("delivery_estimate") if isinstance(r, dict) else r.delivery_estimate
        short_description = r.get("short_description") if isinstance(r, dict) else r.short_description
        link = r.get("link") if isinstance(r, dict) else r.link
        ranking_meta = ranking_lookup.get((str(name), str(retailer)), {})
        cart_items.append(
            {
                "id": f"{_slugify(name)}-{idx}",
                "title": name,
                "price": price,
                "currency": "USD",
                "image": image_url,
                "retailer": retailer,
                "deliveryEstimate": delivery_estimate,
                "shortDescription": short_description,
                "variant": {
                    "size": size_value,
                    "color": color_value,
                    "material": material_value,
                },
                "link": link,
                "url": link,
                "verified": False,
                "rankingScore": ranking_meta.get("score"),
                "rankingRank": ranking_meta.get("rank"),
                "llmExplanation": ranking_meta.get("llm_explanation"),
                "whyLocal": ranking_meta.get("why_local"),
            }
        )

    total_price = round(sum(item["price"] for item in cart_items), 2)
    return {"items": cart_items, "totalPrice": total_price}
