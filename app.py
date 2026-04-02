"""
app.py
PPTAgent — Streamlit 앱 진입점
FRONTEND.md의 4단계 위자드 구조 구현
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


import streamlit as st

st.set_page_config(
    page_title="PPTAgent",
    page_icon="📊",
    layout="centered",
)


def init_session() -> None:
    """세션 상태 초기화"""
    defaults = {
        "step": 1,
        "selected_template": None,
        "user_input": {},
        "slide_schema": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_progress_bar(current_step: int) -> None:
    """상단 진행 바 렌더링"""
    steps = ["1. 템플릿 선택", "2. 내용 입력", "3. 구조 확인", "4. 완료"]
    cols = st.columns(len(steps))
    for i, (col, label) in enumerate(zip(cols, steps), start=1):
        with col:
            if i < current_step:
                st.markdown(f"✅ ~~{label}~~")
            elif i == current_step:
                st.markdown(f"**🔵 {label}**")
            else:
                st.markdown(f"⬜ {label}")
    st.divider()


def render_step_1() -> None:
    """Step 1: 템플릿 선택"""
    st.title("어떤 장표를 만들까요?")

    templates = [
        {"id": "weekly_report", "icon": "📋", "name": "주간/월간 업무 보고"},
        {"id": "project_status", "icon": "📊", "name": "프로젝트 현황 보고"},
        {"id": "proposal", "icon": "💡", "name": "신규 기획안 제안"},
        {"id": "data_report", "icon": "📈", "name": "데이터 분석 리포트"},
    ]

    cols = st.columns(2)
    for i, tmpl in enumerate(templates):
        with cols[i % 2]:
            selected = st.session_state.selected_template == tmpl["id"]
            border = "2px solid #2E75B6" if selected else "1px solid #D9D9D9"
            if st.button(
                f"{tmpl['icon']} {tmpl['name']}",
                key=f"tmpl_{tmpl['id']}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.selected_template = tmpl["id"]
                st.rerun()

    st.write("")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("다음 →", type="primary", use_container_width=True):
            if not st.session_state.selected_template:
                st.error("템플릿을 선택해주세요.")
            else:
                st.session_state.step = 2
                st.rerun()


def render_step_2() -> None:
    """Step 2: 내용 입력 (템플릿별 폼)"""
    template = st.session_state.selected_template

    template_names = {
        "weekly_report": "주간/월간 업무 보고",
        "project_status": "프로젝트 현황 보고",
        "proposal": "신규 기획안 제안",
        "data_report": "데이터 분석 리포트",
    }
    st.title(f"내용을 입력해주세요")
    st.caption(f"선택한 템플릿: {template_names.get(template, template)}")

    inputs = {}

    if template == "weekly_report":
        inputs["period"] = st.text_input(
            "보고 기간 *",
            placeholder="예) 2024년 10월 4주차",
            value=st.session_state.user_input.get("period", ""),
        )
        inputs["done"] = st.text_area(
            "이번 주 주요 업무 *",
            placeholder="예)\n- VoC 대시보드 데이터 업데이트\n- 주간 보고서 작성",
            value=st.session_state.user_input.get("done", ""),
            height=150,
        )
        inputs["plan"] = st.text_area(
            "다음 주 계획 *",
            placeholder="예)\n- 신규 기능 기획안 작성\n- 팀 미팅 준비",
            value=st.session_state.user_input.get("plan", ""),
            height=120,
        )
        inputs["issues"] = st.text_area(
            "이슈 / 특이사항 (선택)",
            placeholder="예) 일정 지연 가능성 있음 → 대응 방안 검토 중",
            value=st.session_state.user_input.get("issues", ""),
            height=100,
        )
        required = ["period", "done", "plan"]

    elif template == "project_status":
        inputs["project_name"] = st.text_input(
            "프로젝트명 *",
            value=st.session_state.user_input.get("project_name", ""),
        )
        inputs["period"] = st.text_input(
            "프로젝트 기간 *",
            placeholder="예) 2024.09 ~ 2024.12",
            value=st.session_state.user_input.get("period", ""),
        )
        inputs["goal"] = st.text_area(
            "프로젝트 목표 *",
            height=100,
            value=st.session_state.user_input.get("goal", ""),
        )
        inputs["progress"] = st.text_area(
            "현재 진행 현황 *",
            height=120,
            value=st.session_state.user_input.get("progress", ""),
        )
        inputs["risks"] = st.text_area(
            "리스크 / 이슈 (선택)",
            height=100,
            value=st.session_state.user_input.get("risks", ""),
        )
        required = ["project_name", "period", "goal", "progress"]

    elif template == "proposal":
        inputs["background"] = st.text_area(
            "제안 배경 / 문제 정의 *",
            height=120,
            value=st.session_state.user_input.get("background", ""),
        )
        inputs["solution"] = st.text_area(
            "솔루션 / 핵심 내용 *",
            height=120,
            value=st.session_state.user_input.get("solution", ""),
        )
        inputs["effect"] = st.text_area(
            "기대 효과 *",
            height=100,
            value=st.session_state.user_input.get("effect", ""),
        )
        inputs["resources"] = st.text_area(
            "필요 자원 / 실행 계획 (선택)",
            height=100,
            value=st.session_state.user_input.get("resources", ""),
        )
        required = ["background", "solution", "effect"]

    elif template == "data_report":
        inputs["title"] = st.text_input(
            "분석 제목 *",
            placeholder="예) 2024 Q3 고객 분석 결과",
            value=st.session_state.user_input.get("title", ""),
        )
        inputs["background"] = st.text_area(
            "분석 배경 및 목적 *",
            height=100,
            value=st.session_state.user_input.get("background", ""),
        )
        uploaded = st.file_uploader(
            "데이터 파일 업로드 (CSV / JSON, 선택)",
            type=["csv", "json"],
        )
        if uploaded:
            inputs["uploaded_file_name"] = uploaded.name
            st.success(f"✅ {uploaded.name} 업로드 완료")
        inputs["direction"] = st.text_area(
            "개선 방향 (선택)",
            height=100,
            value=st.session_state.user_input.get("direction", ""),
        )
        required = ["title", "background"]

    else:
        st.error("알 수 없는 템플릿입니다.")
        required = []

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("다음 →", type="primary", use_container_width=True):
            missing = [k for k in required if not inputs.get(k, "").strip()]
            if missing:
                st.error("필수 항목을 모두 입력해주세요.")
            else:
                st.session_state.user_input = inputs
                st.session_state.step = 3
                st.rerun()


def render_step_3() -> None:
    """Step 3: AI 슬라이드 기획 + 구조 미리보기"""
    st.title("슬라이드 구조를 확인해주세요")

    # 아직 슬라이드 기획이 안 됐으면 AI 호출
    if st.session_state.slide_schema is None:
        with st.spinner("슬라이드 구조를 기획하는 중이에요..."):
            try:
                from core.llm.claude import ClaudeAdapter
                adapter = ClaudeAdapter()
                user_request = "\n".join([
                    f"{k}: {v}"
                    for k, v in st.session_state.user_input.items()
                    if v
                ])
                schema = adapter.plan_slides(
                    user_request=user_request,
                    template=st.session_state.selected_template,
                )
                st.session_state.slide_schema = schema
                st.rerun()
            except Exception as e:
                st.error(str(e))
                if st.button("다시 시도"):
                    st.rerun()
                return

    schema = st.session_state.slide_schema
    st.success(f"총 {len(schema.slides)}장의 슬라이드가 생성됩니다")

    type_labels = {
        "title": "표지", "section": "섹션", "bullet": "불릿",
        "chart": "차트", "table": "표", "two_column": "2단",
        "image": "이미지", "blank": "빈 슬라이드",
    }

    for slide in schema.slides:
        title = (
            slide.content.title
            or slide.content.heading
            or "(제목 없음)"
        )
        type_label = type_labels.get(slide.type.value, slide.type.value)
        st.markdown(f"**{slide.index}.** {title} `{type_label}`")

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 내용 수정", use_container_width=True):
            st.session_state.slide_schema = None
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("장표 생성하기 →", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


def render_step_4() -> None:
    """Step 4: .pptx 생성 및 다운로드"""
    st.title("장표가 완성됐어요! 🎉")

    schema = st.session_state.slide_schema

    with st.spinner("장표를 만들고 있어요..."):
        try:
            from core.renderer import render_pptx
            pptx_bytes = render_pptx(schema)
        except Exception as e:
            st.error(f"파일 생성에 실패했어요. 잠시 후 다시 시도해주세요.\n\n오류: {str(e)}")
            if st.button("다시 시도"):
                st.session_state.step = 3
                st.rerun()
            return

    file_name = f"{schema.meta.title}.pptx"
    st.download_button(
        label="⬇️ 다운로드",
        data=pptx_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary",
        use_container_width=True,
    )

    st.write("")
    st.divider()
    if st.button("+ 새 장표 만들기", use_container_width=True):
        for key in ["step", "selected_template", "user_input", "slide_schema"]:
            st.session_state.pop(key, None)
        st.rerun()


def main() -> None:
    """앱 메인 진입점"""
    init_session()
    render_progress_bar(st.session_state.step)

    step = st.session_state.step
    if step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3()
    elif step == 4:
        render_step_4()


if __name__ == "__main__":
    main()
