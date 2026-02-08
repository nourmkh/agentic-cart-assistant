from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ranking_service import process_and_rank, process_from_extract_and_results

router = APIRouter(prefix="/api/ranking", tags=["ranking"])


class RankingRequest(BaseModel):
    products_data: Dict[str, Any]
    client_data: Dict[str, Any]
    zep_persona: Dict[str, Any]


class RankingFromExtractRequest(BaseModel):
    extract: Dict[str, Any]
    results: List[Dict[str, Any]]


@router.post("/process")
async def rank_products(payload: RankingRequest):
    try:
        return process_and_rank(payload.products_data, payload.client_data, payload.zep_persona)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-extract")
async def rank_from_extract(payload: RankingFromExtractRequest):
    try:
        return process_from_extract_and_results(payload.extract, payload.results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
