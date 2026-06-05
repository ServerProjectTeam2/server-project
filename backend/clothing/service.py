import json
import os
from typing import List
from backend.clothing.schema import ClothingItem

CLOTHES_FILE = "backend/clothing/clothes.json"

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
