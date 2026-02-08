from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data.llm_extractor import extract_user_requirements

router = APIRouter(prefix="/api/llm", tags=["llm"])


class LlmExtractRequest(BaseModel):
    query: str
    preferences: list[str] = []


class LlmExtractResponse(BaseModel):
    data: Dict[str, Any]


@router.post("/extract", response_model=LlmExtractResponse)
def extract_requirements(payload: LlmExtractRequest):
    try:
        data = extract_user_requirements(payload.query, payload.preferences)
        return {"data": data}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("LLM extraction failed")
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {exc}")
