from app.services.ranking_service import process_and_rank


if __name__ == "__main__":
    # Minimal demo runner; all logic lives in app.services.ranking_service
    demo_products = {
        "query": "ski outfit size M budget 400 waterproof",
        "items": {
            "jacket": [
                {"name": "Columbia Whirlibird IV", "price": 179.99, "delivery_days": 3, "retailer": "Amazon", "style": "casual", "color": "black"},
                {"name": "Patagonia PowSlayer", "price": 299.00, "delivery_days": 2, "retailer": "REI", "style": "sporty", "color": "blue"},
            ],
            "pants": [
                {"name": "Columbia Bugaboo IV", "price": 89.99, "delivery_days": 4, "retailer": "Amazon", "style": "minimaliste", "color": "grey"},
            ],
        },
    }
    demo_client = {"budget": 400.0, "delivery_deadline": 5.0, "preferences_clicked": ["Budget", "My Style"]}
    demo_persona = {"preferred_styles": ["minimaliste", "sporty"], "preferred_colors": ["blue", "black"]}

    result = process_and_rank(demo_products, demo_client, demo_persona)
    print(result)