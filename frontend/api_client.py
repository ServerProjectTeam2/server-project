from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import requests


BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 15


def health_check() -> Dict[str, Any]:
    return _request("GET", "/health")


def get_clothes() -> List[Dict[str, Any]] | Dict[str, Any]:
    result = _request("GET", "/clothing/")
    return result if isinstance(result, list) else result


def load_default_wardrobe() -> Dict[str, Any]:
    return _request("POST", "/clothing/load-samples")


def load_sample_clothes() -> Dict[str, Any]:
    return load_default_wardrobe()


def add_clothing(
    category: str,
    color: str,
    thickness: str,
    material: Optional[str] = None,
    tags: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    tag_list = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]
    payload = {
        "items": [
            {
                "category": category,
                "color": color,
                "thickness": thickness,
                "material": material or None,
                "tags": tag_list,
                "description": description or None,
            }
        ],
        "source": "manual",
    }
    return _request("POST", "/clothing/manual-input", json=payload)


def upload_and_analyze_clothing(image_file: str) -> Dict[str, Any]:
    if not image_file:
        return {"error": "분석할 이미지를 업로드해 주세요."}

    try:
        with open(image_file, "rb") as file:
            files = {"file": (image_file.split("\\")[-1].split("/")[-1], file, "image/jpeg")}
            return _request("POST", "/clothing/upload-and-analyze", files=files, timeout=60)
    except OSError as exc:
        return {"error": f"이미지 파일을 읽을 수 없습니다: {exc}"}


def get_weather(place: str) -> Dict[str, Any]:
    return _request("GET", "/weather/current", params={"place": place})


def get_recommendation(city: str, activity_env: str, preferred_style: str) -> Dict[str, Any]:
    payload = {
        "city": city,
        "activity_env": activity_env,
        "preferred_style": preferred_style,
    }
    return _request("POST", "/recommendation/predict", json=payload, timeout=30)


def analyze_outfit_chat(
    message: str,
    city: str = "서울",
    activity_env: str = "실외",
    preferred_style: str = "캐주얼",
) -> str:
    """
    자연어 옷 조합 상담용 응답을 생성합니다.
    FastAPI 날씨/추천 API를 우선 사용하고, 실패해도 시연 가능한 fallback 답변을 반환합니다.
    """
    selected_place = _infer_place(message) or city or "서울 송파구"
    weather = get_weather(selected_place)
    recommendation = get_recommendation(selected_place, activity_env, preferred_style)
    use_closet = should_use_closet(message)
    wardrobe = []
    if use_closet:
        wardrobe = get_clothes()
        if isinstance(wardrobe, dict) or not wardrobe:
            wardrobe = []

    weather_error = isinstance(weather, dict) and weather.get("error")
    if weather_error:
        weather = {
            "location": {"name": selected_place},
            "temperature": 22.0,
            "apparent_temperature": 22.0,
            "relative_humidity": None,
            "weather_description": "날씨 API fallback",
            "precipitation": 0.0,
            "source": "fallback",
        }

    temp = _to_float(weather.get("apparent_temperature") or weather.get("temperature"), 22.0)
    outfit_text = message.strip() or "입력한 옷 조합"
    wardrobe_matches = _find_wardrobe_matches(outfit_text, wardrobe) if use_closet else []
    wardrobe_recs = _recommend_from_wardrobe(wardrobe, temp, outfit_text) if use_closet else []
    score = _score_outfit(outfit_text, temp, activity_env)
    feels = _build_feels(outfit_text, temp, activity_env)
    problems = _build_problems(outfit_text, temp, activity_env)
    recs = _build_recommendations(temp, activity_env)
    style_tip = _style_tip(outfit_text, temp, preferred_style)

    if isinstance(recommendation, dict) and not recommendation.get("error"):
        recs.extend(
            item
            for item in [
                recommendation.get("top"),
                recommendation.get("bottom"),
                recommendation.get("outer"),
                recommendation.get("acc"),
            ]
            if item and item not in recs and "등록된" not in item
        )

    weather_note = ""
    if weather_error:
        weather_note = "\n\n참고: 날씨 API 호출에 실패해 기본 날씨값으로 분석했습니다."

    closet_section = ""
    if use_closet:
        closet_section = f"**옷장 참고**\n{_format_wardrobe_reference(wardrobe, wardrobe_matches)}\n\n"

    recommendation_title = "옷장에서 추천한 코디" if use_closet else "추천 코디"
    recommendation_items = wardrobe_recs if use_closet and wardrobe_recs else recs

    return (
        f"현재 {weather.get('location', {}).get('name', selected_place)} 날씨는 "
        f"약 {temp:.0f}도, 상태는 {weather.get('weather_description', '정보 없음')}입니다.\n\n"
        f"{closet_section}"
        f"**코디 적합도: {score}점**\n\n"
        f"**예상 체감**\n{_bullet_list(feels)}\n\n"
        f"**문제점**\n{_bullet_list(problems)}\n\n"
        f"**{recommendation_title}**\n{_bullet_list(recommendation_items)}\n\n"
        f"**한 줄 스타일 팁**\n{style_tip}"
        f"{weather_note}"
    )


def _request(method: str, path: str, timeout: int = TIMEOUT, **kwargs):
    try:
        response = requests.request(method, f"{BASE_URL}{path}", timeout=timeout, **kwargs)
        data = response.json()
        if response.ok:
            return data
        return {"error": data.get("detail", "요청 처리 중 오류가 발생했습니다.")}
    except requests.RequestException as exc:
        return {"error": f"FastAPI 서버 연결 실패: {exc}"}
    except ValueError:
        return {"error": "서버 응답을 JSON으로 해석할 수 없습니다."}


def _infer_place(message: str) -> Optional[str]:
    match = re.search(r"([가-힣A-Za-z]+(?:시|도)?\s+[가-힣A-Za-z]+(?:구|군|동|읍|면|역))", message)
    if match:
        return match.group(1)

    places = ["잠실역", "강남역", "홍대입구역", "서울 송파구", "서울 강동구", "부산 해운대구"]
    for place in places:
        if place in message:
            return place

    cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "제주", "수원", "춘천", "청주", "전주", "강릉"]
    for city in cities:
        if city in message:
            return city

    match = re.search(r"([가-힣A-Za-z]+)(?:인데|에서| 날씨|이야|야)", message)
    return match.group(1) if match else None


def should_use_closet(message: str) -> bool:
    keywords = [
        "옷장",
        "내 옷",
        "내옷",
        "내가 가진 옷",
        "가지고 있는 옷",
        "등록한 옷",
        "내 옷장에서",
        "내 옷들",
        "내옷들",
        "보유한 옷",
    ]
    normalized = message.replace(" ", "")
    return any(keyword in message or keyword.replace(" ", "") in normalized for keyword in keywords)


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _score_outfit(outfit: str, temp: float, activity_env: str) -> int:
    score = 75
    text = outfit.lower()
    heavy = ["후드", "후드티", "니트", "맨투맨", "패딩", "코트", "기모", "두꺼운"]
    light = ["반팔", "린넨", "얇은", "반바지", "민소매"]
    dark = ["검정", "블랙", "black"]
    long_bottom = ["청바지", "긴바지", "데님"]

    if temp >= 28:
        if any(word in text for word in heavy):
            score -= 30
        if any(word in text for word in long_bottom):
            score -= 10
        if any(word in text for word in dark):
            score -= 10
        if any(word in text for word in light):
            score += 10
    elif temp <= 8:
        if any(word in text for word in light):
            score -= 25
        if any(word in text for word in heavy):
            score += 15
    elif 18 <= temp < 25:
        score += 5

    if activity_env == "실외" and temp >= 26:
        score -= 10

    return max(0, min(100, score))


def _item_label(item: Dict[str, Any]) -> str:
    return item.get("description") or " ".join(
        str(part) for part in [item.get("color"), item.get("material"), item.get("category")] if part
    )


def _find_wardrobe_matches(outfit: str, wardrobe: List[Dict[str, Any]]) -> List[str]:
    text = outfit.lower()
    matches = []
    for item in wardrobe:
        fields = [
            item.get("description") or "",
            item.get("category") or "",
            item.get("color") or "",
            item.get("material") or "",
            " ".join(item.get("tags") or []),
        ]
        haystack = " ".join(fields).lower()
        if any(word and word in text for word in haystack.split()):
            matches.append(_item_label(item))
    return matches[:5]


def _recommend_from_wardrobe(wardrobe: List[Dict[str, Any]], temp: float, outfit: str) -> List[str]:
    if not wardrobe:
        return []

    top_items = [item for item in wardrobe if item.get("category") == "상의"]
    bottom_items = [item for item in wardrobe if item.get("category") == "하의"]
    outer_items = [item for item in wardrobe if item.get("category") == "아우터"]

    if temp >= 28:
        top = _first_by_keywords(top_items, ["얇음", "반팔", "여름"]) or _first_item(top_items)
        bottom = _first_by_keywords(bottom_items, ["얇음", "반바지", "여름", "베이지"]) or _first_item(bottom_items)
        return [f"{_item_label(top)} + {_item_label(bottom)}"] if top and bottom else []

    if temp >= 20:
        top = _first_by_keywords(top_items, ["얇음", "면", "캐주얼"]) or _first_item(top_items)
        bottom = _first_by_keywords(bottom_items, ["보통", "청바지", "캐주얼"]) or _first_item(bottom_items)
        outer = _first_by_keywords(outer_items, ["얇음", "바람막이"])
        combo = f"{_item_label(top)} + {_item_label(bottom)}" if top and bottom else None
        return [combo, f"추우면 {_item_label(outer)}를 추가"] if combo and outer else ([combo] if combo else [])

    top = _first_by_keywords(top_items, ["두꺼움", "후드", "니트"]) or _first_item(top_items)
    bottom = _first_item(bottom_items)
    outer = _first_item(outer_items)
    combo = f"{_item_label(top)} + {_item_label(bottom)}" if top and bottom else None
    return [combo, f"외출 시 {_item_label(outer)} 추가"] if combo and outer else ([combo] if combo else [])


def _first_by_keywords(items: List[Dict[str, Any]], keywords: List[str]):
    for item in items:
        haystack = " ".join(
            [
                item.get("description") or "",
                item.get("color") or "",
                item.get("thickness") or "",
                item.get("material") or "",
                " ".join(item.get("tags") or []),
            ]
        )
        if any(keyword in haystack for keyword in keywords):
            return item
    return None


def _first_item(items: List[Dict[str, Any]]):
    return items[0] if items else None


def _format_wardrobe_reference(wardrobe: List[Dict[str, Any]], matches: List[str]) -> str:
    if not wardrobe:
        return "- 옷장 데이터가 없어 기본 날씨 기준으로 분석했습니다."
    preview = [_item_label(item) for item in wardrobe[:5]]
    lines = [f"- 옷장에서 {', '.join(preview)} 등을 확인했습니다."]
    if matches:
        lines.append(f"- 질문과 관련된 옷: {', '.join(matches)}")
    return "\n".join(lines)


def _build_feels(outfit: str, temp: float, activity_env: str) -> List[str]:
    text = outfit.lower()
    feels = []
    if temp >= 28:
        feels.append("기온이 높아 실외에서는 더위를 크게 느낄 수 있습니다.")
        if "후드" in text or "후드티" in text:
            feels.append("후드티는 통풍이 제한되어 땀이 날 가능성이 큽니다.")
        if "검정" in text or "블랙" in text:
            feels.append("검정 계열은 햇빛을 받으면 열 흡수가 높을 수 있습니다.")
    elif temp <= 8:
        feels.append("낮은 기온이라 보온성이 부족하면 춥게 느껴질 수 있습니다.")
    else:
        feels.append("현재 기온에서는 두께감만 맞으면 비교적 무난합니다.")
    if activity_env == "실내":
        feels.append("실내 활동이라면 냉방 여부에 따라 얇은 겉옷이 도움이 됩니다.")
    return feels


def _build_problems(outfit: str, temp: float, activity_env: str) -> List[str]:
    text = outfit.lower()
    problems = []
    if temp >= 28 and ("후드" in text or "후드티" in text or "니트" in text):
        problems.append("기온에 비해 상의가 두꺼운 편입니다.")
    if temp >= 26 and ("청바지" in text or "긴바지" in text):
        problems.append("긴바지는 실외 활동 시 답답하거나 땀이 찰 수 있습니다.")
    if activity_env == "실외" and temp >= 26:
        problems.append("실외 활동 시간이 길면 체감 더위가 더 커질 수 있습니다.")
    if not problems:
        problems.append("큰 문제는 없지만 활동 시간과 냉난방 환경을 함께 고려하세요.")
    return problems


def _build_recommendations(temp: float, activity_env: str) -> List[str]:
    if temp >= 28:
        return ["반팔 티셔츠", "얇은 셔츠", "밝은 색상의 하의", "통풍이 좋은 소재"]
    if temp >= 23:
        return ["얇은 긴팔 또는 반팔", "가벼운 면바지", "밝거나 중간 톤 색상", "얇은 겉옷은 선택"]
    if temp >= 16:
        return ["긴팔 티셔츠", "가벼운 셔츠", "청바지 또는 면바지", "얇은 가디건"]
    if temp >= 8:
        return ["맨투맨 또는 니트", "자켓", "긴바지", "얇은 머플러 또는 가디건"]
    return ["두꺼운 아우터", "니트 또는 기모 상의", "보온성 있는 하의", "목도리나 장갑"]


def _style_tip(outfit: str, temp: float, preferred_style: str) -> str:
    if temp >= 28:
        return f"{preferred_style} 무드는 살리되, 어두운 두꺼운 옷보다 밝고 얇은 소재로 바꾸면 훨씬 쾌적합니다."
    return f"{preferred_style} 스타일을 유지하면서 색상은 2~3개 안에서 맞추면 코디가 더 정돈돼 보입니다."


def _bullet_list(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
