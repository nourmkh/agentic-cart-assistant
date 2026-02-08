from .state import AgentState
from .store import get_wallet


def build_initial_state(user_id: str) -> AgentState:
    wallet = get_wallet(user_id)
    if not wallet:
        return AgentState(user_id=user_id, budget_limit=None, wallet_balance=0.0, currency="USD")
    return AgentState(
        user_id=wallet.user_id,
        budget_limit=wallet.budget_limit,
        wallet_balance=wallet.wallet_balance,
        currency=wallet.currency,
    )
