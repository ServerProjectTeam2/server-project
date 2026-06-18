#옷 정보 받아서 저장

from typing import List
from fastapi import APIRouter, UploadFile, File
from backend.clothing.schema import ClothingItem, WardrobeInput
from backend.clothing.service import save_clothes, save_image, load_clothes, delete_clothing
from backend.clothing.vision import analyze_clothing_image

router = APIRouter(prefix="/clothing", tags=["clothing"])

@router.get("/", response_model=List[ClothingItem])
async def get_all_clothing():
    """저장된 모든 옷 목록을 조회합니다."""
    return load_clothes()

@router.delete("/{item_id}")
async def delete_clothing_item(item_id: str):
    """특정 ID의 옷 정보를 삭제합니다."""
    updated_wardrobe = delete_clothing(item_id)
    return {
        "status": "success",
        "message": f"Item with ID {item_id} deleted.",
        "total_count": len(updated_wardrobe)
    }

@router.post("/upload-and-analyze")
async def upload_and_analyze_clothing(file: UploadFile = File(...)):
    """
    이미지를 업로드하고 AI가 자동으로 옷의 정보를 분석합니다.
    (윤재건 파트: 이미지 처리 및 정보 추출)
    """
    # 1. 이미지 파일 읽기
    content = await file.read()
    
    # 2. Vision AI로 이미지 분석 (clothing/vision.py 사용)
    analysis = analyze_clothing_image(content)
    
    # 3. 이미지 파일 저장
    file.file.seek(0)
    file_path = save_image(file)
    
    return {
        "status": "success",
        "analysis": analysis,
        "image_path": file_path,
        "message": "이미지 분석이 완료되었습니다. 추출된 정보를 확인해주세요."
    }

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