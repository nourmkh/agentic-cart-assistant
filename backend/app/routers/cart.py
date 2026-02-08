import json
import re
from pathlib import Path

from fastapi import APIRouter

from app.data.search_cache import get_last_search
from app.services.RetailProduct import search_products

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


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
    last = get_last_search()
    if last and not any([budget, deadline, size, style, target, color, items]):
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
        results, _debug = await search_products(
            budget=budget,
            deadline=deadline,
            size=size,
            style=style,
            target=target,
            color=color,
            items=item_list,
        )

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
                "verified": False,
            }
        )

    total_price = round(sum(item["price"] for item in cart_items), 2)
    return {"items": cart_items, "totalPrice": total_price}
