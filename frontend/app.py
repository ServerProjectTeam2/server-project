from __future__ import annotations

import gradio as gr

try:
    from frontend.api_client import (
        add_clothing,
        analyze_outfit_chat,
        get_clothes,
        load_default_wardrobe,
        upload_and_analyze_clothing,
    )
except ModuleNotFoundError:
    from api_client import (
        add_clothing,
        analyze_outfit_chat,
        get_clothes,
        load_default_wardrobe,
        upload_and_analyze_clothing,
    )


def chat_consult(message, history, city, activity_env, preferred_style, image_file):
    message = message.strip()
    if not message and not image_file:
        return history, "", None

    image_context = ""
    image_summary = ""
    if image_file:
        image_result = upload_and_analyze_clothing(image_file)
        image_summary = _format_image_analysis(image_result)
        analysis = image_result.get("analysis") if isinstance(image_result, dict) else None
        if analysis:
            image_context = (
                "\n\n업로드한 옷 이미지 분석 결과: "
                f"카테고리 {analysis.get('category', '-')}, "
                f"색상 {analysis.get('color', '-')}, "
                f"두께 {analysis.get('thickness', '-')}, "
                f"소재 {analysis.get('material', '-')}, "
                f"태그 {', '.join(analysis.get('tags') or [])}, "
                f"설명 {analysis.get('description', '-')}"
            )

    user_text = message or "업로드한 옷 이미지로 오늘 코디가 괜찮은지 분석해줘."

    reply = analyze_outfit_chat(
        message=f"{user_text}{image_context}",
        city=city,
        activity_env=activity_env,
        preferred_style=preferred_style,
    )
    if image_summary:
        reply = f"**업로드 이미지 분석**\n{image_summary}\n\n{reply}"

    history = history or []
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    return history, "", None


def format_current_settings(city, activity_env, preferred_style):
    return f"**현재 설정**  \n{city or '서울 송파구'} | {activity_env or '실외'} | {preferred_style or '캐주얼'}"


def submit_clothing(category, color, thickness, material, tags, description):
    result = add_clothing(category, color, thickness, material, tags, description)
    if result.get("error"):
        return result["error"], format_clothes()
    return f"등록 완료: 총 {result.get('total_count', 0)}개", format_clothes()


def load_default_wardrobe_to_ui():
    result = load_default_wardrobe()
    clothes_text = format_clothes()
    if result.get("error"):
        return result["error"], clothes_text
    return f"{result.get('message', '내 옷장을 불러왔습니다.')}\n현재 등록된 옷: {result.get('total_count', 0)}개", clothes_text


def analyze_image(image_file):
    result = upload_and_analyze_clothing(image_file)
    return _format_image_analysis(result)


def _format_image_analysis(result):
    if result.get("error"):
        return result["error"]

    analysis = result.get("analysis") or {}
    tags = analysis.get("tags") or []
    if isinstance(tags, list):
        tags = ", ".join(str(tag) for tag in tags)

    return (
        f"카테고리: {analysis.get('category', '-')}\n"
        f"색상: {analysis.get('color', '-')}\n"
        f"두께: {analysis.get('thickness', '-')}\n"
        f"소재: {analysis.get('material', '-')}\n"
        f"태그: {tags or '-'}\n"
        f"설명: {analysis.get('description', '-')}\n"
        f"이미지 경로: {result.get('image_path', '-')}"
    )


def format_clothes():
    clothes = get_clothes()
    if isinstance(clothes, dict) and clothes.get("error"):
        return clothes["error"]
    if not clothes:
        return "등록된 옷이 없습니다. 내 옷장을 불러오거나 직접 옷을 등록해 주세요."

    lines = []
    for idx, item in enumerate(clothes, start=1):
        tags = ", ".join(item.get("tags") or [])
        name = item.get("description") or item.get("category", "-")
        lines.append(
            f"{idx}. {name} / {item.get('category', '-')} / {item.get('color', '-')} / "
            f"{item.get('thickness', '-')} / {item.get('material') or '-'} / {tags or '-'}"
        )
    return "\n".join(lines)


EXAMPLE_1 = "오늘 검정 후드티랑 청바지 입어도 될까?"
EXAMPLE_2 = "반팔에 청바지 입어도 괜찮을까?"
EXAMPLE_3 = "오늘 날씨에 어울리는 캐주얼 코디 추천해줘"


with gr.Blocks(title="AI 코디 상담 챗봇") as demo:
    gr.Markdown(
        """
        # AI 코디 상담 챗봇
        지역과 지금 입으려는 옷 조합을 말하면, 날씨를 반영해 코디 적합도와 개선안을 분석합니다.
        """
    )

    with gr.Tab("AI 코디 상담"):
        settings_summary = gr.Markdown(format_current_settings("서울 송파구", "실외", "캐주얼"))
        with gr.Accordion("설정 변경", open=False):
            with gr.Row():
                city = gr.Textbox(value="서울 송파구", label="지역/동네")
                activity_env = gr.Radio(["실외", "실내"], value="실외", label="활동 환경")
                preferred_style = gr.Textbox(value="캐주얼", label="선호 스타일")

        chatbot = gr.Chatbot(label="코디 상담", height=410, autoscroll=True)

        with gr.Row():
            example_1 = gr.Button(EXAMPLE_1)
            example_2 = gr.Button(EXAMPLE_2)
            example_3 = gr.Button(EXAMPLE_3)

        with gr.Row():
            chat_image = gr.Image(label="옷 이미지 업로드 (선택)", type="filepath", height=170, scale=1)
            user_message = gr.Textbox(
            label="질문",
            placeholder="예: 오늘 검정 후드티랑 청바지 입어도 될까?",
            lines=5,
            scale=2,
        )

        with gr.Row():
            send_button = gr.Button("상담하기", variant="primary")
            clear_button = gr.Button("대화 초기화")

        example_1.click(lambda: EXAMPLE_1, outputs=user_message)
        example_2.click(lambda: EXAMPLE_2, outputs=user_message)
        example_3.click(lambda: EXAMPLE_3, outputs=user_message)

        for setting_input in [city, activity_env, preferred_style]:
            setting_input.change(
                format_current_settings,
                inputs=[city, activity_env, preferred_style],
                outputs=settings_summary,
            )

        send_button.click(
            chat_consult,
            inputs=[user_message, chatbot, city, activity_env, preferred_style, chat_image],
            outputs=[chatbot, user_message, chat_image],
        )
        user_message.submit(
            chat_consult,
            inputs=[user_message, chatbot, city, activity_env, preferred_style, chat_image],
            outputs=[chatbot, user_message, chat_image],
        )
        clear_button.click(lambda: [], outputs=chatbot)

    with gr.Tab("보조: 옷장 관리"):
        gr.Markdown("등록한 옷을 조회하거나 내 옷장을 불러와 옷장 기반 추천에 사용할 수 있습니다.")
        gr.Markdown("### 수동 옷 등록")

        with gr.Row():
            category = gr.Dropdown(["상의", "하의", "아우터", "신발", "기타"], value="상의", label="카테고리")
            color = gr.Textbox(value="검정", label="색상")
            thickness = gr.Dropdown(["얇음", "보통", "두꺼움"], value="보통", label="두께")

        material = gr.Textbox(label="소재", placeholder="면, 울, 데님 등")
        tags = gr.Textbox(label="태그", placeholder="캐주얼, 데일리")
        description = gr.Textbox(label="설명", placeholder="선택 입력")
        add_status = gr.Textbox(label="등록 결과", interactive=False)
        clothes_view = gr.Textbox(label="옷 목록", lines=10, interactive=False)

        gr.Button("옷 등록").click(
            submit_clothing,
            inputs=[category, color, thickness, material, tags, description],
            outputs=[add_status, clothes_view],
        )
        gr.Button("내 옷장 불러오기").click(
            load_default_wardrobe_to_ui,
            outputs=[add_status, clothes_view],
        )


if __name__ == "__main__":
    demo.launch()
