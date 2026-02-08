from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.data.budget_agent.store import upsert_wallet, get_wallet, update_wallet_balance
from app.data.budget_agent.graph import run_budget_flow

router = APIRouter(prefix="/api/budget", tags=["budget"])


class BudgetSetRequest(BaseModel):
    user_id: str = "demo"
    budget_limit: float
    currency: str = "USD"


class BudgetStatusResponse(BaseModel):
    user_id: str
    budget_limit: Optional[float]
    wallet_balance: float
    currency: str


class BudgetProposeRequest(BaseModel):
    user_id: str = "demo"
    amount: float
    item_name: str


class BudgetConfirmRequest(BaseModel):
    user_id: str = "demo"
    amount: float


@router.post("/set", response_model=BudgetStatusResponse)
def set_budget(payload: BudgetSetRequest):
    record = upsert_wallet(
        user_id=payload.user_id,
        wallet_balance=payload.budget_limit,
        currency=payload.currency,
        budget_limit=payload.budget_limit,
    )
    return {
        "user_id": record.user_id,
        "budget_limit": record.budget_limit,
        "wallet_balance": record.wallet_balance,
        "currency": record.currency,
    }


@router.get("/status", response_model=BudgetStatusResponse)
def budget_status(user_id: str = "demo"):
    record = get_wallet(user_id) or upsert_wallet(user_id=user_id, wallet_balance=0.0, currency="USD")
    return {
        "user_id": record.user_id,
        "budget_limit": record.budget_limit,
        "wallet_balance": record.wallet_balance,
        "currency": record.currency,
    }


@router.post("/propose")
def propose_purchase(payload: BudgetProposeRequest):
    return run_budget_flow(
        user_id=payload.user_id,
        action="propose_purchase",
        amount=payload.amount,
        item_name=payload.item_name,
    )


@router.post("/confirm", response_model=BudgetStatusResponse)
def confirm_purchase(payload: BudgetConfirmRequest):
    record = get_wallet(payload.user_id) or upsert_wallet(
        user_id=payload.user_id,
        wallet_balance=0.0,
        currency="USD",
    )
    new_balance = record.wallet_balance - payload.amount
    updated = update_wallet_balance(payload.user_id, new_balance)
    return {
        "user_id": updated.user_id,
        "budget_limit": updated.budget_limit,
        "wallet_balance": updated.wallet_balance,
        "currency": updated.currency,
    }
