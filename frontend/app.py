from __future__ import annotations

import gradio as gr


def recommend_outfit(location: str, image):
    if not location:
        return "지역을 입력해주세요."

    result = f"""
[입력 정보]

- 지역 : {location}

[추천 결과]

현재 날씨와 업로드한 옷 정보를 기반으로 추천 결과를 제공합니다.

- 날씨 정보
- 옷 이미지 분석 결과
- 추천 점수
- 최종 코디 추천 문구

* 현재는 UI 화면 구성 단계이며 추후 백엔드 API와 연결하여 실제 추천 결과를 출력할 예정입니다.
"""
    return result


with gr.Blocks(title="Weather Clothing Recommendation") as demo:
    gr.Markdown("# 날씨 기반 의상 추천 서비스")
    gr.Markdown("날씨 정보와 옷 이미지를 활용하여 적절한 코디를 추천합니다.")

    location = gr.Textbox(
        label="지역 입력",
        placeholder="예) Seoul, Stockholm, Linkoping"
    )

    outfit_image = gr.Image(
        label="옷 이미지 업로드",
        type="pil"
    )

    recommend_button = gr.Button("추천받기")

    result = gr.Textbox(
        label="추천 결과",
        lines=10
    )

    recommend_button.click(
        fn=recommend_outfit,
        inputs=[location, outfit_image],
        outputs=result
    )


if __name__ == "__main__":
    demo.launch()

