from typing import Optional

from .store import get_wallet


def manage_wallet(user_id: str, action: str, amount: Optional[float] = None, item_name: Optional[str] = None) -> str:
    """
    Manage the user's fashion wallet.
    - action='check': Check the current balance.
    - action='propose_purchase': Suggest buying an item. This WILL NOT subtract money,
      but will trigger a confirmation modal on the frontend.
    """
    wallet = get_wallet(user_id)
    if not wallet:
        return "User not found."

    if action == "check":
        return f"Balance: {wallet.wallet_balance} {wallet.currency}."

    if action == "propose_purchase":
        if amount is None or item_name is None:
            return "Missing amount/item."
        if wallet.wallet_balance < amount:
            return (
                f"[BUDGET_EXCEEDED] item='{item_name}' price={amount} "
                f"balance={wallet.wallet_balance} currency='{wallet.currency}'"
            )
        return (
            f"[WALLET_CONFIRMATION_REQUIRED] item='{item_name}' price={amount} "
            f"currency='{wallet.currency}'"
        )

    return "Invalid action."
