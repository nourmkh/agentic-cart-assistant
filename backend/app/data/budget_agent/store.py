from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class WalletRecord:
    user_id: str
    wallet_balance: float
    currency: str
    budget_limit: Optional[float] = None


_WALLETS: Dict[str, WalletRecord] = {}


def get_wallet(user_id: str) -> Optional[WalletRecord]:
    return _WALLETS.get(user_id)


def upsert_wallet(user_id: str, wallet_balance: float, currency: str, budget_limit: Optional[float] = None) -> WalletRecord:
    record = WalletRecord(
        user_id=user_id,
        wallet_balance=wallet_balance,
        currency=currency,
        budget_limit=budget_limit,
    )
    _WALLETS[user_id] = record
    return record


def update_wallet_balance(user_id: str, new_balance: float) -> Optional[WalletRecord]:
    record = _WALLETS.get(user_id)
    if not record:
        return None
    record.wallet_balance = new_balance
    return record
