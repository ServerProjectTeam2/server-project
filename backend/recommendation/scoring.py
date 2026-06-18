from typing import Any, Dict, List, Optional
from backend.clothing.schema import ClothingItem
from backend.weather.schema import CurrentWeather

# 색상 조화 사전 정의
COLOR_GROUPS = {
    "무채색": ["흰색", "검정", "회색", "아이보리", "베이지"],
    "유채색_따뜻함": ["빨강", "주황", "노랑", "브라운", "카키"],
    "유채색_시원함": ["파랑", "네이비", "초록", "보라", "민트"]
}

def check_color_harmony(color1: str, color2: str) -> float:
    """
    두 색상 간의 조화 점수를 반환합니다. (0.0 ~ 1.0)
    """
    # 1. 동일 색상 (톤온톤 후보)
    if color1 == color2:
        return 1.0
    
    # 2. 무채색 포함 여부 (무채색은 어디든 잘 어울림)
    if color1 in COLOR_GROUPS["무채색"] or color2 in COLOR_GROUPS["무채색"]:
        return 0.9
    
    # 3. 같은 그룹 내의 색상 (유사색 조화)
    for group in COLOR_GROUPS.values():
        if color1 in group and color2 in group:
            return 0.8
            
    return 0.5

def calculate_item_score(
    item: ClothingItem, 
    weather: CurrentWeather, 
    preferred_style: str, 
    activity_env: str
) -> float:
    """
    개별 의류 아이템에 대해 날씨와 사용자 환경에 따른 적합도 점수를 계산합니다.
    (100점 만점 기준)
    """
    score = 0.0
    # 체감온도(apparent_temperature)를 우선적으로 사용하고, 없으면 일반 기온 사용
    temp = weather.apparent_temperature if weather.apparent_temperature is not None else (weather.temperature or 20.0)

    # 1. 기온별 두께감 적합도 (최대 60점)
    if temp < 5:  # 매우 추움 (패딩, 목도리 등)
        if item.thickness == "두꺼움": score += 60
        elif item.thickness == "보통": score += 20
        elif item.thickness == "얇음": score -= 30
    elif 5 <= temp < 9:  # 추움 (코트, 가죽자켓 등)
        if item.thickness == "두꺼움": score += 60
        elif item.thickness == "보통": score += 40
        elif item.thickness == "얇음": score -= 10
    elif 9 <= temp < 12:  # 쌀쌀함 (트렌치코트, 점퍼 등)
        if item.thickness == "보통": score += 60
        elif item.thickness == "두꺼움": score += 40
        elif item.thickness == "얇음": score += 20
    elif 12 <= temp < 17:  # 선선함 (자켓, 가디건, 맨투맨 등)
        if item.thickness == "보통": score += 60
        elif item.thickness == "얇음": score += 40
        elif item.thickness == "두꺼움": score += 20
    elif 17 <= temp < 20:  # 온화함 (니트, 가디건, 청바지 등)
        if item.thickness == "보통": score += 40
        elif item.thickness == "얇음": score += 60
        elif item.thickness == "두꺼움": score -= 10
    elif 20 <= temp < 23:  # 쾌적함 (긴팔티, 면바지 등)
        if item.thickness == "얇음": score += 60
        elif item.thickness == "보통": score += 30
        elif item.thickness == "두꺼움": score -= 20
    elif 23 <= temp < 28:  # 반소매 날씨 (반팔, 반바지 등)
        if item.thickness == "얇음": score += 60
        elif item.thickness == "보통": score += 10
        elif item.thickness == "두꺼움": score -= 40
    else:  # 28도 이상 한여름 (민소매, 반바지 등)
        if item.thickness == "얇음": score += 60
        elif item.thickness == "보통": score -= 20
        elif item.thickness == "두꺼움": score -= 60

    # 2. 스타일 적합도 (최대 20점)
    if preferred_style.lower() in [tag.lower() for tag in item.tags]:
        score += 20
    elif any(tag in item.tags for tag in ["기본", "데일리", "심플"]):
        score += 10  # 선호 스타일이 아니더라도 범용적인 옷은 가점

    # 3. 색상 범용성 점수 (추가: 최대 10점)
    if item.color in COLOR_GROUPS["무채색"]:
        score += 10  # 무채색은 코디하기 쉬우므로 가점
    
    # 4. 활동 환경 및 기타 상황 (최대 10점)
    if activity_env == "실내":
        if item.thickness == "얇음":
            score += 5
        if item.category == "아우터" and "가디건" in (item.material or ""):
            score += 5
    
    if activity_env == "실외":
        if "방한" in item.tags or "방풍" in item.tags:
            score += 5
        if temp < 10 and item.thickness == "두꺼움":
            score += 5

    # 5. 강수 정보 반영
    precip_prob = weather.daily_precipitation_probability or 0
    if precip_prob > 50:
        if "방수" in item.tags or "레인" in item.tags:
            score += 15
        if item.material == "가죽" or item.material == "스웨이드":
            score -= 20
        if item.color == "흰색":
            score -= 10  # 비오는 날 오염되기 쉬운 흰색 옷 감점

    # 최종 점수 정규화 (0 ~ 100점 사이로 제한)
    return max(0.0, min(100.0, score))

def get_top_scored_items(
    clothes: List[ClothingItem], 
    weather: CurrentWeather, 
    preferred_style: str, 
    activity_env: str,
    top_n: int = 5
) -> List[ClothingItem]:
    """
    모든 옷에 점수를 매기고, 카테고리별로 상위 N개의 아이템만 추출합니다.
    """
    # 점수 부여
    scored_items = []
    for item in clothes:
        score = calculate_item_score(item, weather, preferred_style, activity_env)
        scored_items.append((item, score))
    
    # 점수 높은 순으로 정렬
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    # 카테고리별로 분류하여 상위 N개 추출
    categories = ["상의", "하의", "아우터", "기타"]
    final_candidates = []
    
    for cat in categories:
        cat_items = [item for item, score in scored_items if item.category == cat]
        final_candidates.extend(cat_items[:top_n])
        
    return final_candidates


def build_fallback_recommendation(
    clothes: List[ClothingItem],
    reason: str = "LLM 추천을 사용할 수 없어 점수 기반 기본 추천을 반환했습니다.",
) -> Dict[str, Any]:
    """
    추천 실패 상황에서도 response_model에 맞는 최소 코디를 반환합니다.
    """
    top = _pick_item(clothes, "상의") or "등록된 상의 없음"
    bottom = _pick_item(clothes, "하의") or "등록된 하의 없음"
    outer = _pick_item(clothes, "아우터")
    acc = _pick_item(clothes, "기타") or _pick_item(clothes, "신발")

    return {
        "top": top,
        "bottom": bottom,
        "outer": outer,
        "acc": acc,
        "reason": reason,
        "style_tip": "날씨와 활동 환경을 고려해 두께감이 맞는 옷을 우선 선택했습니다.",
    }


def _pick_item(clothes: List[ClothingItem], category: str):
    for item in clothes:
        if item.category == category:
            parts = [item.color, item.material, item.category]
            return " ".join(part for part in parts if part) or item.category
    return None
