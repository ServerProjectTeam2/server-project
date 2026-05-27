# schemas/clothing.py
from pydantic import BaseModel
from typing import Optional, List

class ClothingItem(BaseModel):
    category: str        # "상의" | "하의" | "아우터" | "신발" | "기타"
    color: str           # "흰색", "검정" 등
    thickness: str       # "얇음" | "보통" | "두꺼움"
    material: Optional[str] = None   # "면", "울", "패딩" 등
    tags: List[str] = []             # ["캐주얼", "방한"] 등

class WardrobeInput(BaseModel):
    items: List[ClothingItem]
    source: str = "manual"   # "manual" | "image"
