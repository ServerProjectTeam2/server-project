import os
import json
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from backend.llm.prompts import SYSTEM_PROMPT, RECOMMENDATION_PROMPT_TEMPLATE
from backend.weather.schema import CurrentWeather
from backend.clothing.schema import ClothingItem

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class LLMService:
    def __init__(self):
        # 환경 변수에서 설정 로드
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            # API 키가 없을 경우 경고 메시지 출력 또는 예외 처리
            print("Warning: GROQ_API_KEY is not set.")
        
        self.model_name = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b")
        
        # ChatGroq 클라이언트 초기화
        self.llm = ChatGroq(
            temperature=0.7,
            model_name=self.model_name,
            groq_api_key=self.api_key
        )

    async def generate_recommendation(
        self, 
        weather: CurrentWeather, 
        clothes: List[ClothingItem],
        activity_env: str = "실외",
        preferred_style: str = "캐주얼"
    ) -> Dict[str, Any]:
        """
        날씨와 의류 데이터를 분석하여 Groq LLM을 통해 JSON 형식의 코디 추천을 생성합니다.
        """
        # 의류 리스트를 XML/JSON 태그 구조로 변환
        clothing_list_str = "\n".join([
            f"<item id='{item.id}'>category: {item.category}, color: {item.color}, material: {item.material or 'N/A'}, thickness: {item.thickness}, tags: {', '.join(item.tags)}</item>"
            for item in clothes
        ])

        user_prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
            weather_desc=weather.weather_description or "정보 없음",
            temp=weather.temperature if weather.temperature is not None else "N/A",
            apparent_temp=weather.apparent_temperature if weather.apparent_temperature is not None else "N/A",
            precip_prob=weather.daily_precipitation_probability if weather.daily_precipitation_probability is not None else 0,
            activity_env=activity_env,
            preferred_style=preferred_style,
            clothing_list=clothing_list_str
        )

        try:
            # ChatGroq 호출
            messages = [
                ("system", SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
            
            response = self.llm.invoke(messages)
            
            # JSON 파싱 시도 (LLM이 JSON 형식을 잘 지켰을 경우)
            try:
                content = response.content.strip()
                # 마크다운 코드 블록 제거
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                return json.loads(content)
            except json.JSONDecodeError:
                # 파싱 실패 시 원문 반환 또는 기본 구조 반환
                return {
                    "raw_response": response.content,
                    "error": "JSON parsing failed"
                }

        except Exception as e:
            return {
                "error": str(e),
                "fallback": "LLM 호출 중 오류가 발생했습니다."
            }

# 싱글톤 인스턴스
llm_service = LLMService()
