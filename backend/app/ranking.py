from typing import Dict, List, Any
import os
import sys
from dotenv import load_dotenv

# Import Groq client for llama-3.1-8b-instant LLM
try:
    from groq import Groq  # type: ignore
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    Groq = None  # type: ignore

# Load environment variables
load_dotenv()

# Groq API key from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️  WARNING: GROQ_API_KEY not found in .env. LLM explanations will use fallback.")
    print("   Add to .env: GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")


# =============================================================================
# FONCTION SCORE PRODUIT (inchangée, déterministe)
# =============================================================================

def score_product(
    product: Dict[str, Any],
    weights: Dict[str, float],
    budget: float,
    max_delivery_days: float
) -> Dict[str, Any]:
    price_score = max(0.0, 1.0 - (product["price"] / budget)) if budget > 0 else 0.5
    delivery_score = max(0.0, (max_delivery_days - product["delivery_days"]) / max_delivery_days) if max_delivery_days > 0 else 0.5
    style_score = product.get("preference_match", 0.5)

    final_score = (
        weights.get("price", 0.33)    * price_score +
        weights.get("delivery", 0.33) * delivery_score +
        weights.get("style", 0.34)    * style_score
    )

    decomposition = {
        "price_contrib":    round(weights.get("price", 0.33)    * price_score,    3),
        "delivery_contrib": round(weights.get("delivery", 0.33) * delivery_score, 3),
        "style_contrib":    round(weights.get("style", 0.34)    * style_score,    3),
    }

    contribs = [(k.split('_')[0], v) for k, v in decomposition.items()]
    strongest = max(contribs, key=lambda x: x[1])
    why_local = f"boosted mainly by {strongest[0]} ({strongest[1]:.3f}) as it contributes the most to the score"

    return {
        "product": product,
        "score": round(final_score, 3),
        "decomposition": decomposition,
        "why_local": why_local
    }


# =============================================================================
# POIDS SELON PRÉFÉRENCES (inchangé)
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
# MATCH STYLE DYNAMIQUE (inchangé)
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
# FALLBACK EXPLANATION (sans LLM)
# =============================================================================

def _generate_fallback_explanation(best: Dict[str, Any], category: str, weights: Dict[str, float], preferences: List[str]) -> str:
    p = best["product"]
    decomp = best["decomposition"]

    contribs = [
        ("price", decomp.get("price_contrib", 0)),
        ("delivery", decomp.get("delivery_contrib", 0)),
        ("style", decomp.get("style_contrib", 0))
    ]
    strongest_factor, strongest_value = max(contribs, key=lambda x: x[1])

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
    else:  # style
        match_score = p.get("preference_match", 0)
        explanations.append(f"This product closely matches your preferences ({match_score*100:.0f}% match).")
        if decomp.get("style_contrib", 0) > 0.3:
            explanations.append("Strong style alignment contributed most to its #1 ranking.")

    explanations.append(f"Final score: {best.get('score', 0):.3f} (weighted across all criteria).")

    return " ".join(explanations)


# =============================================================================
# EXPLICATION VIA GROQ (llama-3.1-8b-instant)
# =============================================================================

def generate_llm_explanation(best: Dict[str, Any], category: str, weights: Dict[str, float], preferences: List[str]) -> str:
    """Call Groq llama-3.1-8b-instant to generate a short English explanation.
    
    Falls back to local explanation if API key missing or any error occurs.
    """
    # Build prompt from product data
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
    
    except Exception as e:
        print(f"Groq API error: {e}")
        return _generate_fallback_explanation(best, category, weights, preferences)
# =============================================================================
# FONCTION PRINCIPALE : SCORING + AFFICHAGE (avec Grok pour explication #1)
# =============================================================================

def process_and_rank(
    products_data: Dict[str, Any],
    client_data: Dict[str, Any],
    zep_persona: Dict[str, Any]
):
    budget = client_data.get("budget", 400.0)
    max_delivery_days = client_data.get("delivery_deadline", 5.0)
    preferences = client_data.get("preferences_clicked", [])

    weights = get_weights(preferences)
    pref_str = ', '.join(preferences) or "no preference → balanced"

    print(f"\n{'='*70}")
    print(f"CLIENT QUERY: {products_data.get('query', 'Not specified')}")
    print(f"BUDGET: {budget} € | MAX DELIVERY: {max_delivery_days} days")
    print(f"CLICKED PREFERENCES: {pref_str}")
    print(f"WEIGHTS → price: {weights['price']:.0%} | delivery: {weights['delivery']:.0%} | style: {weights['style']:.0%}")
    print(f"ZEP PERSONA: {zep_persona}")
    print(f"{'='*70}\n")

    results = {}

    for category, products in products_data.get("items", {}).items():
        if not products:
            continue

        # Calcul dynamique du style match
        for p in products:
            p["preference_match"] = calculate_style_match(p, zep_persona)

        scored = [score_product(p, weights, budget, max_delivery_days) for p in products]
        scored.sort(key=lambda x: x["score"], reverse=True)

        results[category] = scored

        print(f"CATEGORY: {category.upper()}  ({len(products)} products)")

        if len(scored) == 0:
            print("  → no products\n")
            continue

        best = scored[0]
        p = best["product"]

        # LLM Explanation via Groq
        llm_explanation = generate_llm_explanation(best, category, weights, preferences)

        # Display #1 product with full details and LLM explanation
        print(f"\n  🏆 #1 RANKED PRODUCT")
        print(f"  {'='*70}")
        print(f"  Name:         {p['name']}")
        print(f"  Retailer:     {p['retailer']}")
        print(f"  Price:        ${p['price']:.2f}")
        print(f"  Delivery:     {p['delivery_days']} day{'s' if p['delivery_days'] != 1 else ''}")
        print(f"  Style Match:  {p['preference_match']*100:.0f}%")
        print(f"  Final Score:  {best['score']:.3f}")
        print(f"  {'='*70}")
        print(f"\n  Why it's #1:")
        print(f"  {llm_explanation}\n")

        # Display #2 and #3 below
        if len(scored) > 1:
            print(f"  Also consider:")
            for i, item in enumerate(scored[1:3], 2):
                p_alt = item["product"]
                print(f"\n    #{i}. {p_alt['name']}")
                print(f"       • {p_alt['retailer']} | ${p_alt['price']:.2f} | {p_alt['delivery_days']} days | {p_alt['preference_match']*100:.0f}% style match")
                print(f"       • Score: {item['score']:.3f}")
            print(f"\n  {'='*70}\n")
        else:
            print(f"  {'='*70}\n")

    return results


# =============================================================================
# DONNÉES DE TEST
# =============================================================================

products_json = {
  "query": "ski outfit size M budget 400 waterproof",
  "items": {
    "jacket": [
      {"name": "Columbia Whirlibird IV", "price": 179.99, "delivery_days": 3, "retailer": "Amazon", "style": "casual", "color": "black"},
      {"name": "Patagonia PowSlayer", "price": 299.00, "delivery_days": 2, "retailer": "REI", "style": "sporty", "color": "blue"},
      {"name": "North Face Freedom", "price": 139.99, "delivery_days": 5, "retailer": "Decathlon", "style": "casual", "color": "blue"}
    ],
    "pants": [
      {"name": "Columbia Bugaboo IV", "price": 89.99, "delivery_days": 4, "retailer": "Amazon", "style": "minimaliste", "color": "grey"},
      {"name": "Patagonia PowSlayer Pants", "price": 249.00, "delivery_days": 2, "retailer": "REI", "style": "minimaliste", "color": "green"}
    ]
  }
}

client_json = {
  "budget": 400.0,
  "delivery_deadline": 5.0,
  "preferences_clicked": ["Budget", "My Style"]
}

zep_persona = {
  "preferred_styles": ["minimaliste", "sporty"],
  "preferred_colors": ["blue", "black"]
}

# =============================================================================
# LANCEMENT
# =============================================================================

if __name__ == "__main__":
    # CLI helper to test the Groq llama-3.1-8b-instant endpoint
    def test_groq_llm():
        if not GROQ_API_KEY:
            print("GROQ_API_KEY not set in .env — cannot test Groq LLM")
            return
        
        if not HAS_GROQ:
            print("Groq package not installed. Run: pip install -r requirements.txt")
            return

        try:
            client = Groq(api_key=GROQ_API_KEY)
            model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Hello from Groq LLM' and nothing else."}],
                temperature=0.0,
                max_tokens=50,
            )
            
            print("✓ Groq connection successful!")
            print(f"Model: {model}")
            print(f"Response: {completion.choices[0].message.content}")
        except Exception as e:
            print(f"✗ Groq API error: {e}")

    if len(sys.argv) > 1 and sys.argv[1] == "test-groq":
        test_groq_llm()
    else:
        process_and_rank(products_json, client_json, zep_persona)