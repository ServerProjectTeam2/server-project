from fastapi import APIRouter, HTTPException
from typing import List, Optional
from backend.llm.service import llm_service
from backend.weather.service import get_current_weather
from backend.clothing.service import load_clothes
from backend.clothing.schema import ClothingItem
from pydantic import BaseModel

router = APIRouter(prefix="/recommendation", tags=["recommendation"])

class RecommendationRequest(BaseModel):
    city: str = "Seoul"
    activity_env: str = "실외"  # "실내" | "실외"
    preferred_style: str = "캐주얼"

class RecommendationResponse(BaseModel):
    top: str
    bottom: str
    outer: Optional[str] = None
    acc: Optional[str] = None
    reason: str
    style_tip: str

@router.post("/predict", response_model=RecommendationResponse)
async def get_clothing_recommendation(request: RecommendationRequest):
    """
    현재 날씨와 내 옷장 데이터를 기반으로 LLM 추천 코디를 생성합니다.
    """
    try:
        # 1. 날씨 데이터 가져오기
        weather_data = get_current_weather(city=request.city)
        
        # 2. 내 옷장 데이터 가져오기
        clothes_data = load_clothes()
        
        # 만약 옷장이 비어있다면 에러 반환
        if not clothes_data:
            raise HTTPException(status_code=404, detail="옷장에 등록된 옷이 없습니다. 먼저 옷을 등록해주세요.")

        # dict 리스트를 ClothingItem 객체 리스트로 변환
        clothes_items = [ClothingItem(**item) for item in clothes_data]

        # 3. 점수 시스템을 사용하여 상위 후보군만 필터링 (LLM 부하 감소 및 정확도 향상)
        filtered_items = get_top_scored_items(
            clothes=clothes_items,
            weather=weather_data,
            preferred_style=request.preferred_style,
            activity_env=request.activity_env,
            top_n=3  # 카테고리별 상위 3개만 LLM에게 전달
        )

        # 4. LLM 서비스 호출하여 추천 사유 및 코디 생성
        recommendation = await llm_service.generate_recommendation(
            weather=weather_data,
            clothes=filtered_items,
            activity_env=request.activity_env,
            preferred_style=request.preferred_style
        )

        return recommendation

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 생성 중 오류 발생: {str(e)}")
