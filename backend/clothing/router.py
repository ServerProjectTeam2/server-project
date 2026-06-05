#옷 정보 받아서 저장

from fastapi import APIRouter, UploadFile, File
from backend.clothing.schema import ClothingItem, WardrobeInput
from backend.clothing.service import save_clothes, save_image

router = APIRouter(prefix="/clothing", tags=["clothing"])

@router.post("/upload-image")
async def upload_clothing_image(file: UploadFile = File(...)):
    # 이미지 파일 저장
    file_path = save_image(file)
    
    return {
        "status": "success",
        "filename": file.filename,
        "file_path": file_path
    }

@router.post("/manual-input")
async def manual_clothing_input(wardrobe: WardrobeInput):
    # 입력받은 옷 데이터를 파일에 저장
    updated_wardrobe = save_clothes(wardrobe.items)
    
    return {
        "status": "success",
        "items": wardrobe.items,
        "total_count": len(updated_wardrobe)
    }