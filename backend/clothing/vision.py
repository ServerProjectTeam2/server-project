import os
import json
import base64
from typing import Dict, Any
from langchain_groq import ChatGroq

def analyze_clothing_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    의류 이미지를 분석하여 속성을 추출합니다. (Vision LLM 사용)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY가 설정되지 않았습니다."}

    # Vision 모델 초기화
    llm = ChatGroq(
        temperature=0.0,
        model_name="llama-3.2-11b-vision-preview",
        groq_api_key=api_key
    )
    
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
            "role": "user",
            "content": [
                {"type": "text", "text": "이 옷의 속성을 분석해줘."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # 마크다운 블록 제거
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
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
