from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

KEY = "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"
MODEL = "openai/gpt-oss-20b"
llm = ChatGroq(temperature=0.7, model_name=MODEL, groq_api_key=KEY)

def generate_coordination_recommendation(weather_info: dict, clothing_info: str):
    # 1. AI에게 정체성과 출력 규칙(JSON)을 부여하는 시스템 프롬프트
    system_prompt = (
        "너는 최고의 패션 스타일리스트이자 기상 분석가야. "
        "입력받은 날씨 정보와 사용자의 옷 설정을 분석해서 오늘 날씨에 이 코디가 적절한지 평가해줘.\n\n"
        "반드시 다른 부연 설명 없이 오직 아래의 JSON 포맷으로만 응답해야 해. 구조를 절대 깨뜨리지 마:\n"
        "{\n"
        "  \"score\": 0부터 100 사이의 정수 점수,\n"
        "  \"perceived_temp\": \"체감 온도 분석 텍스트\",\n"
        "  \"analysis\": \"날씨와 옷 조합에 대한 상세 문제점 분석\",\n"
        "  \"recommendation\": [\"추천 아이템1\", \"추천 아이템2\", \"추천 아이템3\"]\n"
        "}"
    )
    
    # 2. 5번 팀원이 정제해서 넘겨준 데이터를 유저 메시지로 결합
    user_content = (
        f" [날씨 정보]\n기온: {weather_info.get('temp')}도, "
        f"습도: {weather_info.get('humidity')}%, "
        f"상태: {weather_info.get('description')}\n\n"
        f"[선택한 옷]\n{clothing_info}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    # 3. LLM 호출 및 결과 반환
    try:
        response = llm.invoke(messages)
        return response.content  # JSON 문자열이 반환됨
    except Exception as e:
        return f"Error: {str(e)}"