from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentState:
    user_id: str
    budget_limit: Optional[float]
    wallet_balance: float
    currency: str
    days_remaining: Optional[int] = None
