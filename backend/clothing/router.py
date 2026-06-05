#옷 정보 받아서 저장

from fastapi import APIRouter
from backend.clothing.schema import ClothingItem, WardrobeInput
from backend.clothing.service import save_clothes

router = APIRouter(prefix="/clothing", tags=["clothing"])

@router.post("/manual-input")
async def manual_clothing_input(wardrobe: WardrobeInput):
    # 입력받은 옷 데이터를 파일에 저장
    updated_wardrobe = save_clothes(wardrobe.items)
    
    return {
        "status": "success",
        "items": wardrobe.items,
        "total_count": len(updated_wardrobe)
    }