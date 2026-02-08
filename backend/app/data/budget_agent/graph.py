from typing import Dict, Any

from .orchestrator import build_initial_state
from .tools import manage_wallet


def run_budget_flow(user_id: str, action: str, amount: float | None = None, item_name: str | None = None) -> Dict[str, Any]:
    state = build_initial_state(user_id)
    result = manage_wallet(user_id=user_id, action=action, amount=amount, item_name=item_name)
    return {
        "state": state,
        "result": result,
    }
