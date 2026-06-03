#옷 정보 받아서 저장

from fastapi import APIRouter
from backend.clothing.schema import ClothingItem, WardrobeInput

router = APIRouter(prefix="/clothing", tags=["clothing"])

@router.post("/manual-input")
async def manual_clothing_input(wardrobe: WardrobeInput):
    return {
        "status": "success",
        "items": wardrobe.items,
        "total": len(wardrobe.items)
    }