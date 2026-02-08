"""
Shopping search agent: Serper (Google Shopping) API.
Prioritizes trusted retailers first; expands search only if results are insufficient.
"""

import asyncio
import logging
import os
import re
import json
from html.parser import HTMLParser
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from app.schemas.agent import ProductVariants, SearchResultItem


# --- Retailer priority (trusted first, then expand) --------------------------

PRIMARY_RETAILERS = [
    "Zara",
    "H&M",
    "Uniqlo",
    "Pull&Bear",
    "Bershka",
    "Stradivarius",
    "Mango",
    "COS",
    "Massimo Dutti",
    "Nike",
    "Adidas",
    "Puma",
    "New Balance",
    "Reebok",
    "Under Armour",
    "Decathlon",
    "Amazon",
    "ASOS",
    "Zalando",
    "Farfetch",
    "SSENSE",
    "eBay",
    "Uniqlo U",
    "Arket",
    "Banana Republic",
    "Gap",
    "Abercrombie & Fitch",
    "Foot Locker",
    "JD Sports",
    "DSW",
    "Aldo",
    "Clarks",
    "Dr. Martens",
]
PRIMARY_RETAILER_DOMAINS = [
    "zara.com",
    "hm.com",
    "uniqlo.com",
    "pullandbear.com",
    "bershka.com",
    "stradivarius.com",
    "mango.com",
    "cos.com",
    "massimodutti.com",
    "nike.com",
    "adidas.com",
    "puma.com",
    "newbalance.com",
    "reebok.com",
    "underarmour.com",
    "decathlon.com",
    "amazon.com",
    "asos.com",
    "zalando.com",
    "farfetch.com",
    "ssense.com",
    "ebay.com",
    "arket.com",
    "bananarepublic.com",
    "gap.com",
    "abercrombie.com",
    "footlocker.com",
    "jdsports.com",
    "dsw.com",
    "aldo.com",
    "clarks.com",
    "drmartens.com",
]
PRIMARY_RETAILER_DOMAINS = [
    "nike.com",
    "adidas.com",
    "zara.com",
    "hm.com",
    "target.com",
    "uniqlo.com",
    "decathlon.com",
    "amazon.com",
    "asos.com",
]
# Normalized (lower) for matching Serper "source" and domain-derived names
_PRIMARY_NORMALIZED = {s.lower().replace(" ", "") for s in PRIMARY_RETAILERS}
# Also match common variants (e.g. uniqlo.com -> Uniqlo)
_PRIMARY_MATCH_KEYWORDS = [
    "zara",
    "hm",
    "h&m",
    "uniqlo",
    "pull&bear",
    "pullandbear",
    "bershka",
    "stradivarius",
    "mango",
    "cos",
    "massimodutti",
    "massimo",
    "nike",
    "adidas",
    "puma",
    "newbalance",
    "reebok",
    "underarmour",
    "decathlon",
    "amazon",
    "asos",
    "zalando",
    "farfetch",
    "ssense",
    "ebay",
    "arket",
    "bananarepublic",
    "gap",
    "abercrombie",
    "fitch",
    "footlocker",
    "jdsports",
    "dsw",
    "aldo",
    "clarks",
    "drmartens",
]


def _is_primary_retailer(retailer: str) -> bool:
    """True if retailer is in the primary (trusted) list."""
    if not retailer:
        return False
    r = retailer.lower().replace(" ", "").replace("&", "")
    if r in _PRIMARY_NORMALIZED:
        return True
    return any(k in r for k in _PRIMARY_MATCH_KEYWORDS)


def _primary_retailer_rank(retailer: str) -> int:
    """Lower = higher priority. Primary retailers get 0..len-1, others get len."""
    if not retailer:
        return len(PRIMARY_RETAILERS)
    r = retailer.lower().replace(" ", "").replace("&", "")
    for i, name in enumerate(PRIMARY_RETAILERS):
        kn = name.lower().replace(" ", "").replace("&", "")
        if kn in r or r in kn:
            return i
    return len(PRIMARY_RETAILERS)


# --- Parsing helpers ---------------------------------------------------------


def _parse_budget(budget_str: str) -> float | None:
    """Extract numeric budget from strings like '$200', 'under 100', '50 USD'."""
    if not budget_str:
        return None
    numbers = re.findall(r"\d+(?:\.\d+)?", budget_str.replace(",", ""))
    return float(numbers[0]) if numbers else None


def _parse_deadline_days(deadline_str: str) -> int | None:
    """Parse deadline to max delivery days. E.g. '3 days' -> 3, '1 week' -> 7."""
    if not deadline_str:
        return None
    s = deadline_str.strip().lower()
    numbers = re.findall(r"\d+", s)
    n = int(numbers[0]) if numbers else None
    if n is None:
        return None
    if "week" in s:
        return n * 7
    if "month" in s:
        return n * 30
    return n


def _extract_days_from_estimate(estimate: str) -> int | None:
    """Parse '3 days', '2-4 days', '1 week' to a max days number."""
    if not estimate:
        return None
    s = estimate.strip().lower()
    numbers = re.findall(r"\d+", s)
    if not numbers:
        return 7 if "week" in s else None
    max_n = max(int(x) for x in numbers)
    if "week" in s:
        return max_n * 7
    return max_n


# --- Serper (Google Shopping) -------------------------------------------------

# Serper: try google.serper.dev first (common), then serper.dev
SERPER_SHOPPING_URLS = [
    "https://google.serper.dev/shopping",
    "https://serper.dev/shopping",
]
SERPER_SEARCH_URLS = [
    "https://google.serper.dev/search",
    "https://serper.dev/search",
]
TAVILY_SEARCH_URL = "https://api.tavily.com/search"


async def _serper_shopping(query: str, api_key: str, num: int = 20) -> list[dict[str, Any]]:
    """Call Serper Shopping API. Returns list of product-like objects."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    body = {"q": query, "num": num}
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        for url in SERPER_SHOPPING_URLS:
            try:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    "Serper %s: status=%s body=%s",
                    url,
                    e.response.status_code,
                    (e.response.text or "")[:400],
                )
                continue
            except Exception as e:
                last_error = e
                logger.warning("Serper %s request failed: %s", url, e)
                continue
        else:
            if last_error:
                raise last_error
            raise RuntimeError("Serper shopping failed for all endpoints")
    # Response: { "shopping": [ {...}, ... ] } or similar
    shopping = data.get("shopping") or data.get("organic") or data.get("products") or []
    if not isinstance(shopping, list):
        shopping = []
    if not shopping and data:
        logger.info("Serper returned no shopping list; top-level keys: %s", list(data.keys()))
    return shopping


async def _serper_search(query: str, api_key: str, num: int = 3) -> list[dict[str, Any]]:
    """Call Serper Search API. Returns list of organic results."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    body = {"q": query, "num": num}
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        for url in SERPER_SEARCH_URLS:
            try:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    "Serper %s: status=%s body=%s",
                    url,
                    e.response.status_code,
                    (e.response.text or "")[:400],
                )
                continue
            except Exception as e:
                last_error = e
                logger.warning("Serper %s request failed: %s", url, e)
                continue
        else:
            if last_error:
                raise last_error
            raise RuntimeError("Serper search failed for all endpoints")
    organic = data.get("organic") or []
    if not isinstance(organic, list):
        organic = []
    return organic


async def _tavily_search(query: str, api_key: str, num: int = 10) -> list[dict[str, Any]]:
    """Call Tavily Search API. Returns list of result objects."""
    body = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": num,
        "include_images": True,
        "include_answer": False,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(TAVILY_SEARCH_URL, json=body)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results") or []
    if not isinstance(results, list):
        return []
    return results


def _extract_image_url(item: dict[str, Any]) -> str | None:
    """Extract product image URL from Serper/shopping API response (any common field name)."""
    candidates = [
        item.get("image"),
        item.get("imageUrl"),
        item.get("image_url"),
        item.get("thumbnail"),
        item.get("product_image"),
        item.get("image_link"),
        item.get("productImage"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip().startswith(("http://", "https://")):
            return c.strip()
    # Some APIs return thumbnails as a list of URLs
    thumbnails = item.get("thumbnails") or item.get("serpapi_thumbnails")
    if isinstance(thumbnails, list) and thumbnails:
        first = thumbnails[0]
        if isinstance(first, str) and first.strip().startswith(("http://", "https://")):
            return first.strip()
        if isinstance(first, dict) and (first.get("image") or first.get("url")):
            return (first.get("image") or first.get("url") or "").strip() or None
    return None


_COMMON_COLORS = {
    "black",
    "white",
    "gray",
    "grey",
    "blue",
    "navy",
    "red",
    "green",
    "olive",
    "brown",
    "beige",
    "tan",
    "cream",
    "yellow",
    "orange",
    "purple",
    "pink",
    "burgundy",
}



def _clean_variant_value(value: str) -> str | None:
    v = value.strip()
    if not v:
        return None
    lower = v.lower()
    blocked = {
        "select",
        "select size",
        "select color",
        "select colour",
        "choose",
        "choose size",
        "choose color",
        "choose colour",
    }
    if lower in blocked:
        return None
    if lower.startswith("size "):
        v = v[5:].strip()
    return v or None


def _dedupe(values: list[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        if len(out) >= limit:
            break
    return out


def _detect_variant_type(attrs: dict[str, str | None]) -> str | None:
    hay = " ".join(
        str(v).lower()
        for k, v in attrs.items()
        if k in {"name", "id", "aria-label", "data-testid", "class"} and v
    )
    if "size" in hay:
        return "size"
    if "color" in hay or "colour" in hay or "swatch" in hay:
        return "color"
    if "material" in hay or "fabric" in hay:
        return "material"
    return None


class _VariantHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sizes: list[str] = []
        self.colors: list[str] = []
        self.materials: list[str] = []
        self._current_select: str | None = None
        self._in_option = False
        self._option_text: list[str] = []
        self._option_value: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v for k, v in attrs}

        if tag == "select":
            self._current_select = _detect_variant_type(attr_dict)

        if tag == "option":
            self._in_option = True
            self._option_text = []
            self._option_value = attr_dict.get("value")

        for key, value in attr_dict.items():
            if not value:
                continue
            key_lower = key.lower()
            if "data-size" in key_lower:
                v = _clean_variant_value(value)
                if v:
                    self.sizes.append(v)
            if "data-color" in key_lower or "data-colour" in key_lower:
                v = _clean_variant_value(value)
                if v:
                    self.colors.append(v)
            if "data-material" in key_lower:
                v = _clean_variant_value(value)
                if v:
                    self.materials.append(v)

        aria_label = attr_dict.get("aria-label")
        if aria_label:
            class_name = (attr_dict.get("class") or "").lower()
            if "color" in class_name or "colour" in class_name or "swatch" in class_name:
                v = _clean_variant_value(aria_label)
                if v:
                    self.colors.append(v)
            elif aria_label.lower() in _COMMON_COLORS:
                self.colors.append(aria_label.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "option":
            text = "".join(self._option_text).strip()
            raw = self._option_value or text
            value = _clean_variant_value(raw)
            if value and self._current_select:
                if self._current_select == "size":
                    self.sizes.append(value)
                elif self._current_select == "color":
                    self.colors.append(value)
                elif self._current_select == "material":
                    self.materials.append(value)
            self._in_option = False
            self._option_text = []
            self._option_value = None

        if tag == "select":
            self._current_select = None

    def handle_data(self, data: str) -> None:
        if self._in_option:
            self._option_text.append(data)


class _MetaDescriptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.description: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        name = attr_dict.get("name", "").lower()
        prop = attr_dict.get("property", "").lower()
        if name == "description" or prop in {"og:description", "twitter:description"}:
            content = attr_dict.get("content", "").strip()
            if content:
                self.description = content


def _extract_variants_from_html(html: str) -> ProductVariants | None:
    parser = _VariantHTMLParser()
    parser.feed(html)
    sizes = _dedupe([v for v in parser.sizes if v])
    colors = _dedupe([v for v in parser.colors if v])
    materials = _dedupe([v for v in parser.materials if v])
    if not sizes and not colors and not materials:
        return None
    return ProductVariants(sizes=sizes, colors=colors, material=materials)




async def _fetch_variants_from_product_page(
    url: str,
    client: httpx.AsyncClient,
) -> ProductVariants | None:
    if not url:
        return None
    try:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()
        if "html" not in content_type:
            return None
        variants = _extract_variants_from_html(resp.text)
        return variants
    except Exception:
        return None


def _extract_meta_description(html: str) -> str | None:
    parser = _MetaDescriptionParser()
    parser.feed(html)
    return parser.description


async def _resolve_merchant_link(
    title: str,
    source: str,
    api_key: str,
) -> tuple[str | None, str | None]:
    query = f"{title} {source}"
    try:
        results = await _serper_search(query, api_key, num=3)
    except Exception:
        return None, None
    if not results:
        return None, None
    first = results[0] if isinstance(results[0], dict) else None
    if not first:
        return None, None
    link = first.get("link") or first.get("url")
    snippet = first.get("snippet")
    if isinstance(snippet, str):
        snippet = snippet.strip() or None
    else:
        snippet = None
    return link, snippet


def _serper_item_to_result(item: dict[str, Any], retailer: str) -> SearchResultItem | None:
    """Map one Serper shopping item to SearchResultItem. Returns None if invalid."""
    try:
        title = (item.get("title") or item.get("name") or "").strip()
        if not title:
            return None
        # Price: "45.99" or 45.99 or "$45.99" (Serper: price/extractedPrice; SerpAPI: extracted_price)
        raw_price = (
            item.get("price")
            or item.get("extractedPrice")
            or item.get("extracted_price")
            or 0
        )
        if isinstance(raw_price, str):
            raw_price = re.sub(r"[^\d.]", "", raw_price) or "0"
        price = float(raw_price) if raw_price else 0.0
        if price <= 0:
            return None
        delivery = (item.get("delivery") or item.get("delivery_estimate") or "3-5 days").strip()
        image_url = _extract_image_url(item)
        description = (
            item.get("snippet")
            or item.get("description")
            or item.get("richSnippet")
            or item.get("rich_snippet")
        )
        if isinstance(description, dict):
            description = description.get("content") or description.get("text")
        if isinstance(description, list):
            description = " ".join(str(x) for x in description if x)
        if isinstance(description, str):
            description = description.strip() or None
        else:
            description = None

        return SearchResultItem(
            name=title,
            price=round(price, 2),
            delivery_estimate=delivery,
            variants=ProductVariants(
                sizes=item.get("sizes") or [],
                colors=item.get("colors") or [],
                material=item.get("material") or [],
            ),
            retailer=retailer,
            image_url=image_url,
            link=item.get("link") or item.get("url") or item.get("product_url"),
            short_description=description,
        )
    except (TypeError, ValueError):
        return None


def _tavily_item_to_result(item: dict[str, Any]) -> SearchResultItem | None:
    title = (item.get("title") or "").strip()
    if not title:
        return None
    link = item.get("url") or item.get("link")
    description = item.get("content") or item.get("description")
    if isinstance(description, str):
        description = description.strip() or None
    else:
        description = None
    image_url = item.get("image")
    if not isinstance(image_url, str):
        image_url = None
    retailer = _domain_to_retailer(link or "") if link else "Unknown"
    return SearchResultItem(
        name=title,
        price=0.0,
        delivery_estimate="Unknown",
        variants=ProductVariants(sizes=[], colors=[], material=[]),
        retailer=retailer,
        image_url=image_url,
        link=link,
        short_description=description,
    )


def _serper_organic_to_result(item: dict[str, Any]) -> SearchResultItem | None:
    title = (item.get("title") or "").strip()
    link = item.get("link") or item.get("url")
    if not title or not link:
        return None
    snippet = item.get("snippet")
    if isinstance(snippet, str):
        snippet = snippet.strip() or None
    else:
        snippet = None
    retailer = _domain_to_retailer(link)
    return SearchResultItem(
        name=title,
        price=0.0,
        delivery_estimate="Unknown",
        variants=ProductVariants(sizes=[], colors=[], material=[]),
        retailer=retailer,
        image_url=None,
        link=link,
        short_description=snippet,
    )


def _domain_to_retailer(link: str) -> str:
    """Extract retailer name from URL (e.g. amazon.com -> Amazon)."""
    if not link:
        return "Unknown"
    link = link.lower().replace("https://", "").replace("http://", "").split("/")[0]
    # Remove www.
    if link.startswith("www."):
        link = link[4:]
    # Take first part of domain (e.g. amazon.co.uk -> amazon)
    base = link.split(".")[0] if "." in link else link
    return base.capitalize() + ".com"


# --- Mock data (used when no API key or Serper fails) ------------------------

# Placeholder product images: multiple per item so each product gets a different image (Unsplash, no API key)
_MOCK_IMAGES_BY_ITEM: dict[str, list[str]] = {
    "shirt": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400",
        "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=400",
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400",
        "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400",
    ],
    "pants": [
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400",
        "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400",
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400",
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&sat=-100",  # variant
        "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400",
    ],
    "shoes": [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=400",
        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=400",
        "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=400",
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400",
    ],
    "jacket": [
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400",
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400",
        "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=400",
        "https://images.unsplash.com/photo-1578932750294-f5075e85f44a?w=400",
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&sat=-50",
    ],
    "dress": [
        "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
        "https://images.unsplash.com/photo-1595776609370-435704ca2a3c?w=400",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400",
        "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400",
        "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400",
    ],
}
_DEFAULT_MOCK_IMAGES = [
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400",
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
    "https://images.unsplash.com/photo-1491553895911-0055eb64029e?w=400",
    "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400",
]


def _mock_results_for_item(
    item: str,
    style: str,
    size: str,
    max_price: float | None,
    max_days: int | None,
    retailers: list[str],
) -> list[SearchResultItem]:
    """Generate ≥3 mock results for one item from different retailers."""
    base_prices = {"shirt": 29.99, "pants": 44.99, "shoes": 79.99, "jacket": 89.99, "dress": 59.99}
    price = base_prices.get(item.lower(), 39.99)
    if max_price and price > max_price:
        price = min(price, max_price * 0.95)
    results = []
    for i, retailer in enumerate(retailers[:5]):  # up to 5 to have choice
        p = round(price * (0.9 + i * 0.05), 2)
        if max_price and p > max_price:
            continue
        days = (3 + i) if max_days is None else min(3 + i, max_days)
        delivery = f"{days} days"
        image_list = _MOCK_IMAGES_BY_ITEM.get(item.lower(), _DEFAULT_MOCK_IMAGES)
        image_url = image_list[i % len(image_list)]  # different image per product
        results.append(
            SearchResultItem(
                name=f"{style} {item} - {retailer}",
                price=p,
                delivery_estimate=delivery,
                variants=ProductVariants(
                    sizes=[size] if size else ["S", "M", "L"],
                    colors=["black", "navy", "white"],
                    material=["cotton"],
                ),
                retailer=retailer,
                image_url=image_url,
            )
        )
    return results[: max(3, len(retailers))]


def _get_mock_results(
    items: list[str],
    style: str,
    size: str,
    max_price: float | None,
    max_days: int | None,
) -> list[SearchResultItem]:
    """Build mock result list when no API key — generic retailer names only."""
    # Generic labels so we don't specify brands; real retailers come from Serper when API key is set
    generic_retailers = ["Online Store", "Shop", "Retailer", "Store", "Market"]
    out: list[SearchResultItem] = []
    for item in items:
        for p in _mock_results_for_item(item, style, size, max_price, max_days, generic_retailers):
            out.append(p.model_copy(update={"item": item}))
    return out


# --- Search strategy: primary retailers first, then expand --------------------


def _parse_and_filter_raw(
    raw: list[dict[str, Any]],
    max_price: float | None,
    max_days: int | None,
) -> list[SearchResultItem]:
    """Convert raw Serper items to SearchResultItem, apply budget/delivery, sort primary retailers first."""
    candidates: list[SearchResultItem] = []
    for r in raw:
        retailer = (r.get("source") or "").strip() or _domain_to_retailer(r.get("link") or r.get("url") or "")
        parsed = _serper_item_to_result(r, retailer)
        if not parsed:
            continue
        if max_price and parsed.price > max_price:
            continue
        if max_days is not None:
            est = _extract_days_from_estimate(parsed.delivery_estimate)
            if est is not None and est > max_days:
                continue
        candidates.append(parsed)
    # Sort: primary retailers first (by rank), then by retailer name
    candidates.sort(key=lambda x: (_primary_retailer_rank(x.retailer), x.retailer.lower(), x.price))
    return candidates


def _select_per_item(
    candidates: list[SearchResultItem],
    min_retailers: int = 3,
    max_products: int = 5,
) -> list[SearchResultItem]:
    """Pick results: prefer distinct retailers, up to max_products."""
    selected: list[SearchResultItem] = []
    retailers_seen: set[str] = set()
    for p in candidates:
        if len(selected) >= max_products:
            break
        if p.retailer in retailers_seen:
            continue
        retailers_seen.add(p.retailer)
        selected.append(p)

    if len(selected) < max_products:
        for p in candidates:
            if len(selected) >= max_products:
                break
            if p in selected:
                continue
            selected.append(p)
    return selected


def _apply_variant_constraints(
    results: list[SearchResultItem],
    size: str,
    color: str,
) -> None:
    size_term = size.strip() if size else ""
    color_term = color.strip() if color else ""
    for r in results:
        if size_term:
            r.variants.sizes = [size_term]
        if color_term:
            r.variants.colors = [color_term]


def _primary_only_if_any(candidates: list[SearchResultItem]) -> list[SearchResultItem]:
    """Return only primary retailers if any exist; otherwise keep full list."""
    primary = [c for c in candidates if _is_primary_retailer(c.retailer)]
    return primary if primary else candidates


async def _enrich_variants(
    results: list[SearchResultItem],
    api_key: str,
    tavily_key: str,
) -> None:
    to_enrich = [
        r
        for r in results
        if not (r.variants.sizes or r.variants.colors or r.variants.material)
    ]
    if not to_enrich:
        return

    semaphore = asyncio.Semaphore(5)

    async def _bounded_enrich(r: SearchResultItem, client: httpx.AsyncClient) -> ProductVariants | None:
        async with semaphore:
            link = r.link or ""
            if api_key and (not link or "google.com/search" in link):
                resolved_link, snippet = await _resolve_merchant_link(r.name, r.retailer, api_key)
                if resolved_link:
                    r.link = resolved_link
                    link = resolved_link
                if snippet and not r.short_description:
                    r.short_description = snippet

            if tavily_key and (not link or "google.com/search" in link):
                try:
                    t_raw = await _tavily_search(f"{r.name} {r.retailer}", tavily_key, num=3)
                    for t_item in t_raw:
                        t_link = t_item.get("url") or t_item.get("link")
                        if t_link:
                            r.link = t_link
                            link = t_link
                            t_desc = t_item.get("content") or t_item.get("description")
                            if t_desc and not r.short_description:
                                r.short_description = str(t_desc).strip() or r.short_description
                            break
                except Exception:
                    pass

            if link:
                variants = await _fetch_variants_from_product_page(link, client)
                if variants:
                    return variants

                if not r.short_description:
                    try:
                        resp = await client.get(link, follow_redirects=True)
                        resp.raise_for_status()
                        content_type = resp.headers.get("content-type", "").lower()
                        if "html" in content_type:
                            r.short_description = _extract_meta_description(resp.text)
                    except Exception:
                        pass

            return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=12.0, headers=headers) as client:
        tasks = [_bounded_enrich(r, client) for r in to_enrich]
        variants_list = await asyncio.gather(*tasks, return_exceptions=True)

    for r, variants in zip(to_enrich, variants_list):
        if isinstance(variants, ProductVariants):
            r.variants = variants


async def _filter_working_links(results: list[SearchResultItem]) -> list[SearchResultItem]:
    candidates = [r for r in results if r.link]
    if not candidates:
        return []

    # Keep non-Google links without validation to avoid retailer bot blocks.
    non_google = [r for r in candidates if r.link and "google.com/search" not in r.link]
    google = [r for r in candidates if r.link and "google.com/search" in r.link]
    if non_google:
        return non_google

    semaphore = asyncio.Semaphore(6)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async def _check(url: str, client: httpx.AsyncClient) -> bool:
        if not url or "google.com/search" in url:
            return False
        async with semaphore:
            try:
                resp = await client.head(url, follow_redirects=True)
                if resp.status_code < 400:
                    return True
            except Exception:
                pass
            try:
                resp = await client.get(url, follow_redirects=True)
                return resp.status_code < 400
            except Exception:
                return False

    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        link_checks: dict[str, asyncio.Task[bool]] = {}
        for r in google:
            link = r.link or ""
            if link not in link_checks:
                link_checks[link] = asyncio.create_task(_check(link, client))
        link_ok = {link: await task for link, task in link_checks.items()}

    return [r for r in google if r.link and link_ok.get(r.link, False)]


# --- Main entry ---------------------------------------------------------------


async def search_products(
    budget: str,
    deadline: str,
    size: str,
    style: str,
    target: str,
    color: str,
    items: list[str],
) -> tuple[list[SearchResultItem], dict[str, Any]]:
    """
    Shopping search agent: prioritize trusted retailers (Nike, Adidas, Zara, etc.),
    then expand. Filter by budget and delivery. Return ≥3 retailers per item when possible.
    """
    max_price = _parse_budget(budget)
    max_days = _parse_deadline_days(deadline)
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    tavily_key = os.environ.get("TAVILY_API_KEY", "").strip()

    if not items:
        return [], {
            "serper_key_set": bool(api_key),
            "tavily_key_set": bool(tavily_key),
            "items": {},
        }

    all_results: list[SearchResultItem] = []
    debug: dict[str, Any] = {
        "serper_key_set": bool(api_key),
        "tavily_key_set": bool(tavily_key),
        "items": {},
    }

    if api_key:
        for item in items:
            debug_item: dict[str, Any] = {
                "serper_raw": 0,
                "serper_parsed": 0,
                "primary_only": 0,
                "selected_initial": 0,
                "expanded_raw": 0,
                "expanded_parsed": 0,
                "selected_expanded": 0,
                "tavily_raw": 0,
                "tavily_parsed": 0,
                "selected_after_tavily": 0,
                "after_enrich": 0,
                "after_link_filter": 0,
                "serper_organic_raw": 0,
                "serper_organic_parsed": 0,
                "serper_organic_after_link_filter": 0,
                "fallback_organic_used": False,
                "fallback_tavily_used": False,
                "non_google_links": 0,
                "tavily_error": None,
                "serper_organic_error": None,
            }
            seen_key: set[tuple[str, str]] = set()
            unique: list[SearchResultItem] = []

            # 1) First search: scoped to item + style + size + budget (primary retailers prioritized in sort)
            target_term = target.strip() if target else ""
            color_term = color.strip() if color else ""
            query = f"{item} {style} {target_term} {color_term} size {size}".strip()
            if max_price:
                query += f" under ${max_price:.0f}"
            if PRIMARY_RETAILER_DOMAINS:
                site_filters = " OR ".join(f"site:{d}" for d in PRIMARY_RETAILER_DOMAINS)
                query += f" ({site_filters})"
            try:
                raw = await _serper_shopping(query, api_key, num=20)
                debug_item["serper_raw"] = len(raw)
                candidates = _parse_and_filter_raw(raw, max_price, max_days)
                debug_item["serper_parsed"] = len(candidates)
                candidates = _primary_only_if_any(candidates)
                debug_item["primary_only"] = len(candidates)
                for c in candidates:
                    k = (c.name, c.retailer)
                    if k not in seen_key:
                        seen_key.add(k)
                        unique.append(c)
                unique.sort(key=lambda x: (_primary_retailer_rank(x.retailer), x.retailer.lower(), x.price))
                selected = _select_per_item(unique, min_retailers=3)
                debug_item["selected_initial"] = len(selected)

                # 2) If fewer than 5 products, expand search to all websites
                query_expanded = f"buy {item} {style} {target_term} {color_term}".strip()
                if len(selected) < 5:
                    if max_price:
                        query_expanded += f" under ${max_price:.0f}"
                    try:
                        raw2 = await _serper_shopping(query_expanded, api_key, num=25)
                        debug_item["expanded_raw"] = len(raw2)
                        candidates2 = _parse_and_filter_raw(raw2, max_price, max_days)
                        debug_item["expanded_parsed"] = len(candidates2)
                        for c in candidates2:
                            k = (c.name, c.retailer)
                            if k not in seen_key:
                                seen_key.add(k)
                                unique.append(c)
                        unique.sort(key=lambda x: (_primary_retailer_rank(x.retailer), x.retailer.lower(), x.price))
                        selected = _select_per_item(unique, min_retailers=3)
                        debug_item["selected_expanded"] = len(selected)
                    except Exception as e2:
                        logger.warning("Serper expanded search failed for item %r: %s", item, e2)

                if len(selected) < 5 and tavily_key:
                    tavily_query = f"{item} {style} {target_term} {color_term}".strip()
                    if max_price:
                        tavily_query += f" under ${max_price:.0f}"
                    try:
                        t_raw = await _tavily_search(tavily_query, tavily_key, num=10)
                        debug_item["tavily_raw"] = len(t_raw)
                        t_candidates = [r for r in (_tavily_item_to_result(x) for x in t_raw) if r]
                        debug_item["tavily_parsed"] = len(t_candidates)
                        for c in t_candidates:
                            k = (c.name, c.retailer)
                            if k not in seen_key:
                                seen_key.add(k)
                                unique.append(c)
                        unique.sort(key=lambda x: (_primary_retailer_rank(x.retailer), x.retailer.lower(), x.price))
                        selected = _select_per_item(unique, min_retailers=3)
                        debug_item["selected_after_tavily"] = len(selected)
                    except Exception as e3:
                        debug_item["tavily_error"] = str(e3)
                        logger.warning("Tavily search failed for item %r: %s", item, e3)

                await _enrich_variants(selected, api_key, tavily_key)
                _apply_variant_constraints(selected, size, color)
                debug_item["after_enrich"] = len(selected)

                non_google_links = sum(
                    1 for r in selected if r.link and "google.com/search" not in r.link
                )
                debug_item["non_google_links"] = non_google_links

                if non_google_links == 0 and api_key:
                    debug_item["fallback_organic_used"] = True
                    try:
                        organic = await _serper_search(query_expanded, api_key, num=10)
                        debug_item["serper_organic_raw"] = len(organic)
                        organic_items = [r for r in (_serper_organic_to_result(x) for x in organic) if r]
                        debug_item["serper_organic_parsed"] = len(organic_items)
                        if organic_items:
                            selected = _select_per_item(organic_items, min_retailers=3)
                    except Exception as e4:
                        debug_item["serper_organic_error"] = str(e4)
                        logger.warning("Serper organic fallback failed for item %r: %s", item, e4)

                    if len(selected) < 5 and tavily_key:
                        debug_item["fallback_tavily_used"] = True
                        try:
                            t_raw = await _tavily_search(query_expanded, tavily_key, num=10)
                            debug_item["tavily_raw"] = len(t_raw)
                            t_candidates = [r for r in (_tavily_item_to_result(x) for x in t_raw) if r]
                            debug_item["tavily_parsed"] = len(t_candidates)
                            if t_candidates:
                                selected = _select_per_item(t_candidates, min_retailers=3)
                        except Exception as e5:
                            debug_item["tavily_error"] = str(e5)
                            logger.warning("Tavily fallback failed for item %r: %s", item, e5)

                selected = await _filter_working_links(selected)
                debug_item["after_link_filter"] = len(selected)

                debug_item["serper_organic_after_link_filter"] = len(selected)

                for p in selected:
                    all_results.append(p.model_copy(update={"item": item}))
            except Exception as e:
                logger.warning("Serper search failed for item %r: %s", item, e)

            debug["items"][item] = debug_item

    # No mock fallback: return empty results if nothing matches

    # Final filter: budget and delivery
    filtered: list[SearchResultItem] = []
    for r in all_results:
        if max_price and r.price > max_price:
            continue
        if max_days is not None:
            d = _extract_days_from_estimate(r.delivery_estimate)
            if d is not None and d > max_days:
                continue
        filtered.append(r)

    return (filtered if filtered else all_results), debug


def format_search_response_json(results: list[SearchResultItem]) -> str:
    """Return JSON-only response, no extra text (for agent output)."""
    return json.dumps(
        [r.model_dump() for r in results],
        indent=2,
    )
