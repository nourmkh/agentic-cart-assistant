AGENT_LOGS = [
    {"step": 1, "action": "Parsed query", "detail": "Identified 4 product categories from your request", "time": "0.2s"},
    {"step": 2, "action": "Scanned retailers", "detail": "Searched across Amazon, Best Buy, Nike, Everlane + 12 more", "time": "1.1s"},
    {"step": 3, "action": "Ranked 847 items", "detail": "Applied budget, style, and delivery filters", "time": "0.8s"},
    {"step": 4, "action": "Price optimized", "detail": "Found $312 in savings across your cart", "time": "0.3s"},
    {"step": 5, "action": "Verified availability", "detail": "All items in stock with guaranteed delivery dates", "time": "0.5s"},
    {"step": 6, "action": "Cart assembled", "detail": "Top-ranked items selected. Ready for review.", "time": "0.1s"},
]


def get_agent_logs():
    return AGENT_LOGS
