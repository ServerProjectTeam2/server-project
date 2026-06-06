# 의류 속성 모델 정의

from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class ClothingItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())) # 고유 ID 추가
    category: str        # "상의" | "하의" | "아우터" | "신발" | "기타"
    color: str           # "흰색", "검정" 등
    thickness: str       # "얇음" | "보통" | "두꺼움"
    material: Optional[str] = None   # "면", "울", "패딩" 등
    tags: List[str] = []             # ["캐주얼", "방한"] 등
    image_path: Optional[str] = None # 저장된 이미지 경로

class WardrobeInput(BaseModel):
    items: List[ClothingItem]
    source: str = "manual"   # "manual" | "image