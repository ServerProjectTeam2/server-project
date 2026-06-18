from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.llm.service import llm_service
from backend.weather.service import get_current_weather
from backend.weather.schema import CurrentWeather, WeatherLocation
from backend.clothing.service import load_clothes
from backend.clothing.schema import ClothingItem
from backend.recommendation.scoring import build_fallback_recommendation, get_top_scored_items
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
        try:
            weather_data = get_current_weather(city=request.city)
        except Exception:
            weather_data = _fallback_weather(request.city)

        clothes_items = [ClothingItem(**item) for item in load_clothes()]
        filtered_items = get_top_scored_items(
            clothes=clothes_items,
            weather=weather_data,
            preferred_style=request.preferred_style,
            activity_env=request.activity_env,
            top_n=3,
        )

        if not filtered_items:
            return build_fallback_recommendation(
                clothes_items,
                "등록된 옷이 부족해 기본 추천 문구를 반환했습니다.",
            )

        recommendation = await llm_service.generate_recommendation(
            weather=weather_data,
            clothes=filtered_items,
            activity_env=request.activity_env,
            preferred_style=request.preferred_style,
        )

        if _is_valid_recommendation(recommendation):
            return recommendation

        return build_fallback_recommendation(
            filtered_items,
            "LLM 응답 형식이 올바르지 않아 점수 기반 기본 추천을 반환했습니다.",
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            clothes_items = [ClothingItem(**item) for item in load_clothes()]
        except Exception:
            clothes_items = []
        return build_fallback_recommendation(
            clothes_items,
            f"추천 생성 중 오류가 발생해 기본 추천을 반환했습니다: {str(e)}",
        )


def _is_valid_recommendation(recommendation) -> bool:
    if not isinstance(recommendation, dict):
        return False
    return all(recommendation.get(field) for field in ["top", "bottom", "reason", "style_tip"])


def _fallback_weather(city: str) -> CurrentWeather:
    return CurrentWeather(
        location=WeatherLocation(
            name=city or "Seoul",
            country="Korea",
            country_code="KR",
            latitude=37.5665,
            longitude=126.9780,
            nx=60,
            ny=127,
            timezone="Asia/Seoul",
        ),
        temperature=22.0,
        apparent_temperature=22.0,
        relative_humidity=50,
        precipitation=0.0,
        rain=0.0,
        snowfall=0.0,
        weather_code=1,
        weather_description="Clear",
        cloud_cover=0,
        wind_speed=1.0,
        wind_direction=None,
        clothing_hints=["Fallback weather: mild conditions assumed for demo."],
        source="fallback",
    )
