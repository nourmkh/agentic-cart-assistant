from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services.tryon.generator import tryon_generator

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


class TryOnItem(BaseModel):
    id: str | None = None
    image_url: str | None = None
    mask_url: str | None = None
    category: str | None = None
    sub_category: str | None = None
    body_region: str | None = None


class TryOnRequest(BaseModel):
    body_image_url: str
    clothing_items: List[TryOnItem]


@router.post("/generate")
async def generate_tryon(payload: TryOnRequest):
    try:
        result = await tryon_generator.generate_tryon_image(payload.body_image_url, [item.dict() for item in payload.clothing_items])
        if not result:
            raise HTTPException(status_code=500, detail="Try-on generation failed")
        return {"url": result["url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
