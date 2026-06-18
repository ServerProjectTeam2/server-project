import json
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile
from backend.clothing.schema import ClothingItem

BASE_DIR = Path(__file__).resolve().parents[1]
CLOTHES_FILE = BASE_DIR / "clothing" / "clothes.json"
DEFAULT_CLOTHES_FILE = BASE_DIR / "clothing" / "default_clothes.json"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

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
    return _read_clothes_file()

def _read_clothes_file() -> List[dict]:
    if not os.path.exists(CLOTHES_FILE) or os.path.getsize(CLOTHES_FILE) == 0:
        return []
    
    try:
        with open(CLOTHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def load_sample_clothes() -> List[dict]:
    """기본 옷을 기존 옷장에 중복 없이 저장합니다."""
    existing_data = _read_clothes_file()
    updated_data = _merge_default_clothes(existing_data)
    CLOTHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLOTHES_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)
    return updated_data

def _load_default_clothes() -> List[dict]:
    try:
        with open(DEFAULT_CLOTHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _merge_default_clothes(existing_data: List[dict]) -> List[dict]:
    existing_ids = {item.get("id") for item in existing_data}
    existing_descriptions = {item.get("description") for item in existing_data}
    merged = list(existing_data)
    for default_item in _load_default_clothes():
        if default_item.get("id") in existing_ids or default_item.get("description") in existing_descriptions:
            continue
        merged.append(default_item.copy())
    return merged

def save_clothes(new_items: List[ClothingItem]):
    """새로운 옷 목록을 기존 데이터에 추가하여 저장합니다."""
    # 1. 기존 데이터 불러오기
    existing_data = _read_clothes_file()
    
    # 2. Pydantic 모델을 딕셔너리로 변환하여 추가
    for item in new_items:
        existing_data.append(item.model_dump())
    
    # 3. 파일에 저장
    CLOTHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLOTHES_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    
    return existing_data

def delete_clothing(item_id: str) -> List[dict]:
    """특정 ID의 옷 정보와 실제 이미지 파일을 삭제합니다."""
    existing_data = _read_clothes_file()
    
    # 삭제할 아이템 찾기 (이미지 파일 삭제를 위해)
    item_to_delete = next((item for item in existing_data if item.get("id") == item_id), None)
    
    if item_to_delete and item_to_delete.get("image_path"):
        image_path = item_to_delete.get("image_path")
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error deleting file {image_path}: {e}")
    
    # ID가 일치하지 않는 항목만 남깁니다
    updated_data = [item for item in existing_data if item.get("id") != item_id]
    
    if len(existing_data) != len(updated_data):
        CLOTHES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CLOTHES_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
            
    return updated_data
