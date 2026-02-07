from fastapi import APIRouter, HTTPException

from app.data.products import get_products

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def list_products():
    return get_products()


@router.get("/{product_id}")
def get_product(product_id: str):
    products = get_products()
    for p in products:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")
