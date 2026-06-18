import os
import json
import base64
from contextlib import contextmanager
from typing import Dict, Any
from langchain_groq import ChatGroq


DEFAULT_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

def analyze_clothing_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    의류 이미지를 분석하여 속성을 추출합니다. (Vision LLM 사용)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY가 설정되지 않았습니다."}

    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    system_prompt = """
    당신은 의류 분석 전문가입니다. 주어진 사진 속의 옷을 분석하여 아래 JSON 형식으로 응답하세요.
    - category: "상의", "하의", "아우터", "신발", "기타" 중 하나
    - color: 지배적인 색상 (예: "검정", "네이비", "화이트")
    - thickness: "얇음", "보통", "두꺼움" 중 하나
    - material: 주요 소재 (예: "면", "울", "데님", "패딩", "나일론")
    - tags: 스타일이나 특징을 나타내는 태그 리스트 (예: ["캐주얼", "오버핏", "스트릿"])
    - description: 간단한 옷 설명 (1문장)
    
    반드시 순수 JSON만 반환하세요.
    """
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "이 옷의 속성을 분석해줘."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
    ]

    try:
        with _without_proxy_env():
            llm = ChatGroq(
                temperature=0.0,
                model_name=os.getenv("GROQ_VISION_MODEL", DEFAULT_VISION_MODEL),
                groq_api_key=api_key
            )
            response = llm.invoke(messages)
        content = response.content.strip()
        
        # 마크다운 블록 제거
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return _normalize_analysis(json.loads(content))
    except Exception as e:
        print(f"Vision analysis error: {e}")
        return {
            "category": "기타",
            "color": "알수없음",
            "thickness": "보통",
            "material": "알수없음",
            "tags": [],
            "description": f"이미지 분석 실패: {str(e)}"
        }


def _normalize_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    return {
        "category": data.get("category") or "기타",
        "color": data.get("color") or "알수없음",
        "thickness": data.get("thickness") or "보통",
        "material": data.get("material") or "알수없음",
        "tags": tags if isinstance(tags, list) else [],
        "description": data.get("description") or "이미지 분석 결과 설명이 없습니다.",
    }


@contextmanager
def _without_proxy_env():
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    saved = {key: os.environ.get(key) for key in proxy_keys}
    try:
        for key in proxy_keys:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
