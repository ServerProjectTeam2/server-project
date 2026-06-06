import json
import os
import shutil
from typing import List
from fastapi import UploadFile
from backend.clothing.schema import ClothingItem

CLOTHES_FILE = "backend/clothing/clothes.json"
UPLOAD_DIR = "backend/static/uploads"

def save_image(file: UploadFile) -> str:
    """업로드된 이미지를 저장하고 경로를 반환합니다."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def load_clothes() -> List[dict]:
    """저장된 옷 목록을 JSON 파일에서 불러옵니다."""
    if not os.path.exists(CLOTHES_FILE) or os.path.getsize(CLOTHES_FILE) == 0:
        return []
    
    try:
        with open(CLOTHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_clothes(new_items: List[ClothingItem]):
    """새로운 옷 목록을 기존 데이터에 추가하여 저장합니다."""
    # 1. 기존 데이터 불러오기
    existing_data = load_clothes()
    
    # 2. Pydantic 모델을 딕셔너리로 변환하여 추가
    for item in new_items:
        existing_data.append(item.model_dump())
    
    # 3. 파일에 저장
    with open(CLOTHES_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    
    return existing_data

def delete_clothing(item_id: str) -> List[dict]:
    """특정 ID의 옷 정보를 삭제합니다."""
    existing_data = load_clothes()
    
    # ID가 일치하지 않는 항목만 남깁니다 (삭제 로직)
    updated_data = [item for item in existing_data if item.get("id") != item_id]
    
    if len(existing_data) != len(updated_data):
        with open(CLOTHES_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
            
    return updated_data
