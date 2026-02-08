from typing import Dict, List, Any
import os
import logging
import re
from dotenv import load_dotenv

try:
    from groq import Groq  # type: ignore
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    Groq = None  # type: ignore

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# =============================================================================
# SCORE PRODUCT (deterministic)
# =============================================================================

def score_product(
    product: Dict[str, Any],
    weights: Dict[str, float],
    budget: float,
    max_delivery_days: float,
) -> Dict[str, Any]:
    price_score = max(0.0, 1.0 - (product["price"] / budget)) if budget > 0 else 0.5
    delivery_score = max(0.0, (max_delivery_days - product["delivery_days"]) / max_delivery_days) if max_delivery_days > 0 else 0.5
    style_score = product.get("preference_match", 0.5)

    final_score = (
        weights.get("price", 0.33) * price_score
        + weights.get("delivery", 0.33) * delivery_score
        + weights.get("style", 0.34) * style_score
    )

    decomposition = {
        "price_contrib": round(weights.get("price", 0.33) * price_score, 3),
        "delivery_contrib": round(weights.get("delivery", 0.33) * delivery_score, 3),
        "style_contrib": round(weights.get("style", 0.34) * style_score, 3),
    }

    contribs = [(k.split("_")[0], v) for k, v in decomposition.items()]
    strongest = max(contribs, key=lambda x: x[1])
    why_local = f"boosted mainly by {strongest[0]} ({strongest[1]:.3f}) as it contributes the most to the score"

    return {
        "product": product,
        "score": round(final_score, 3),
        "decomposition": decomposition,
        "why_local": why_local,
    }


# =============================================================================
# WEIGHTS FROM PREFERENCES
# =============================================================================

def get_weights(preferences: List[str]) -> Dict[str, float]:
    if not preferences:
        return {"price": 0.33, "delivery": 0.33, "style": 0.34}

    weights = {"price": 0.15, "delivery": 0.15, "style": 0.15}

    for pref in preferences:
        p = pref.lower()
        if "budget" in p or "prix" in p:
            weights["price"] += 0.35
        elif "delivery" in p or "fast" in p or "livraison" in p:
            weights["delivery"] += 0.35
        elif "style" in p or "my style" in p or "look" in p:
            weights["style"] += 0.35

    total = sum(weights.values())
    return {k: round(v / total, 3) for k, v in weights.items()}


# =============================================================================
# STYLE MATCH
# =============================================================================

def calculate_style_match(product: Dict[str, Any], persona: Dict[str, Any]) -> float:
    score = 0.0
    total_weight = 0.0

    product_color = product.get("color", "").lower()
    preferred_colors = persona.get("preferred_colors", [])
    color_match = 1.0 if product_color in [c.lower() for c in preferred_colors] else 0.0
    score += color_match * 0.4
    total_weight += 0.4

    product_style = product.get("style", "").lower()
    preferred_styles = persona.get("preferred_styles", [])
    style_match = 1.0 if product_style in [s.lower() for s in preferred_styles] else 0.0
    score += style_match * 0.6
    total_weight += 0.6

    return round(score / total_weight, 3) if total_weight > 0 else 0.5


# =============================================================================
# FALLBACK EXPLANATION (no LLM)
# =============================================================================

def _generate_fallback_explanation(best: Dict[str, Any], category: str, weights: Dict[str, float], preferences: List[str]) -> str:
    p = best["product"]
    decomp = best["decomposition"]

    contribs = [
        ("price", decomp.get("price_contrib", 0)),
        ("delivery", decomp.get("delivery_contrib", 0)),
        ("style", decomp.get("style_contrib", 0)),
    ]
    strongest_factor, _strongest_value = max(contribs, key=lambda x: x[1])

    explanations = []

    if strongest_factor == "price":
        explanations.append(f"This {category} offers excellent value at ${p.get('price', 0):.2f}.")
        if decomp.get("price_contrib", 0) > 0.3:
            explanations.append("The competitive price significantly boosted its ranking.")
    elif strongest_factor == "delivery":
        delivery_days = p.get("delivery_days", 0)
        explanations.append(f"Fast delivery ({delivery_days} day{'s' if delivery_days != 1 else ''}) makes this a top choice.")
        if decomp.get("delivery_contrib", 0) > 0.2:
            explanations.append("Quick shipping was a key factor in its high ranking.")
    else:
        match_score = p.get("preference_match", 0)
        explanations.append(f"This product closely matches your preferences ({match_score*100:.0f}% match).")
        if decomp.get("style_contrib", 0) > 0.3:
            explanations.append("Strong style alignment contributed most to its #1 ranking.")

    explanations.append(f"Final score: {best.get('score', 0):.3f} (weighted across all criteria).")

    return " ".join(explanations)


# =============================================================================
# LLM EXPLANATION (Groq)
# =============================================================================

def generate_llm_explanation(best: Dict[str, Any], category: str, weights: Dict[str, float], preferences: List[str]) -> str:
    p = best["product"]
    decomp = best["decomposition"]

    prompt = f"""You are an expert shopping assistant. Write a short, natural, and convincing English explanation (3-4 sentences) of why this product is ranked #1 in the "{category}" category.

Product: {p.get('name', 'Unknown')} from {p.get('retailer', 'Unknown retailer')}
Price: ${p.get('price', 0):.2f}
Delivery: {p.get('delivery_days', 0)} days
Style match: {p.get('preference_match', 'N/A')}

Final score: {best.get('score', 0):.3f}

Score breakdown:
- Price contribution: {decomp.get('price_contrib', 0):.3f} (weight {weights.get('price', 0):.0%})
- Delivery contribution: {decomp.get('delivery_contrib', 0):.3f} (weight {weights.get('delivery', 0):.0%})
- Style contribution: {decomp.get('style_contrib', 0):.3f} (weight {weights.get('style', 0):.0%})

User preferences: {', '.join(preferences) or 'balanced'}

Be honest, focus on the strongest factor, use friendly tone. Return only the explanation."""

    if not GROQ_API_KEY or not HAS_GROQ:
        return _generate_fallback_explanation(best, category, weights, preferences)

    try:
        client = Groq(api_key=GROQ_API_KEY)
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )

        return completion.choices[0].message.content.strip()
    except Exception:
        return _generate_fallback_explanation(best, category, weights, preferences)


# =============================================================================
# MAIN PROCESS
# =============================================================================

def process_and_rank(products_data: Dict[str, Any], client_data: Dict[str, Any], zep_persona: Dict[str, Any]) -> Dict[str, Any]:
    budget = client_data.get("budget", 400.0)
    max_delivery_days = client_data.get("delivery_deadline", 5.0)
    preferences = client_data.get("preferences_clicked", [])

    weights = get_weights(preferences)

    results: Dict[str, Any] = {}

    logger.info("[Ranking] start")
    logger.info("[Ranking] budget=%s max_delivery_days=%s preferences=%s", budget, max_delivery_days, preferences)
    logger.info("[Ranking] weights=%s", weights)
    logger.info("[Ranking] persona=%s", zep_persona)

    for category, products in products_data.get("items", {}).items():
        if not products:
            continue

        logger.info("[Ranking] category=%s products=%s", category, len(products))
        for p in products:
            p["preference_match"] = calculate_style_match(p, zep_persona)

        scored = [score_product(p, weights, budget, max_delivery_days) for p in products]
        scored.sort(key=lambda x: x["score"], reverse=True)

        if scored:
            best = scored[0]
            best["llm_explanation"] = generate_llm_explanation(best, category, weights, preferences)
            logger.info(
                "[Ranking] top=%s score=%s price=%s delivery_days=%s",
                best["product"].get("name"),
                best.get("score"),
                best["product"].get("price"),
                best["product"].get("delivery_days"),
            )
            logger.info("[Ranking] top_decomposition=%s", best.get("decomposition"))
            logger.info("[Ranking] top_why_local=%s", best.get("why_local"))
            logger.info("[Ranking] top_llm_explanation=%s", best.get("llm_explanation"))

        # Trace all ranked items (top 5 for clarity)
        for idx, entry in enumerate(scored[:5], start=1):
            product = entry.get("product", {})
            logger.info(
                "[Ranking] #%s name=%s price=%s delivery_days=%s preference_match=%s score=%s decomposition=%s",
                idx,
                product.get("name"),
                product.get("price"),
                product.get("delivery_days"),
                product.get("preference_match"),
                entry.get("score"),
                entry.get("decomposition"),
            )

        results[category] = scored

    return {
        "weights": weights,
        "results": results,
    }


def _parse_budget_value(budget_str: str) -> float | None:
    if not budget_str:
        return None
    numbers = re.findall(r"\d+(?:\.\d+)?", str(budget_str).replace(",", ""))
    return float(numbers[0]) if numbers else None


def _parse_deadline_days(deadline_str: str) -> float | None:
    if not deadline_str:
        return None
    s = str(deadline_str).lower()
    numbers = re.findall(r"\d+", s)
    if numbers:
        n = float(numbers[0])
        if "week" in s:
            return n * 7
        if "month" in s:
            return n * 30
        return n
    return None


def _parse_delivery_days(delivery_estimate: str | None) -> float:
    if not delivery_estimate:
        return 5.0
    s = str(delivery_estimate).lower()
    numbers = re.findall(r"\d+", s)
    if numbers:
        return float(max(int(x) for x in numbers))
    if "tomorrow" in s:
        return 1.0
    return 5.0


def _group_results_by_item(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        item_key = str(r.get("item") or r.get("category") or "other").strip() or "other"
        grouped.setdefault(item_key, []).append(r)
    return grouped


def process_from_extract_and_results(
    extract: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Rank SearchResultItem-style results using LLM extractor output as input."""
    budget_value = _parse_budget_value(str(extract.get("budget", ""))) or 400.0
    deadline_value = _parse_deadline_days(str(extract.get("deadline", ""))) or 5.0
    preferences = extract.get("constraints") or []
    styles = extract.get("style") or []
    colors = extract.get("colors") or []

    client_data = {
        "budget": budget_value,
        "delivery_deadline": deadline_value,
        "preferences_clicked": preferences,
        "query": extract.get("item") or "",
    }
    zep_persona = {
        "preferred_styles": styles,
        "preferred_colors": colors,
    }

    grouped = _group_results_by_item(results)
    products_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for category, items in grouped.items():
        converted: List[Dict[str, Any]] = []
        for item in items:
            converted.append(
                {
                    "name": item.get("name") or item.get("title") or "",
                    "price": float(item.get("price") or 0.0),
                    "delivery_days": _parse_delivery_days(item.get("delivery_estimate") or item.get("deliveryEstimate")),
                    "retailer": item.get("retailer") or "",
                    "style": (styles[0] if styles else ""),
                    "color": (colors[0] if colors else ""),
                }
            )
        products_by_category[category] = converted

    logger.info("[RankingWorkflow] extract=%s", extract)
    logger.info("[RankingWorkflow] grouped_items=%s", {k: len(v) for k, v in products_by_category.items()})

    return process_and_rank({"items": products_by_category, "query": extract.get("item") or ""}, client_data, zep_persona)
