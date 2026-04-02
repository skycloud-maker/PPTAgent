"""Streamlit entrypoint for PPTAgent."""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
from typing import Any

import streamlit as st

from core.llm import get_default_llm
from core.renderer import render_pptx
from core.schema import Slide, SlideSchema

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
SUPPORTED_UPLOAD_TYPES = ("csv", "json")

st.set_page_config(page_title="PPTAgent", page_icon="📊", layout="wide")

TEMPLATES: list[dict[str, str]] = [
    {"id": "weekly_report", "icon": "📅", "name": "주간/월간 업무 보고"},
    {"id": "project_status", "icon": "📌", "name": "프로젝트 현황 보고"},
    {"id": "proposal", "icon": "📝", "name": "신규 기획안 제안"},
    {"id": "data_report", "icon": "📈", "name": "데이터 분석 리포트"},
]
TEMPLATE_NAMES = {template["id"]: template["name"] for template in TEMPLATES}


def init_session() -> None:
    defaults = {
        "step": 1,
        "selected_template": None,
        "user_input": {},
        "uploaded_data": None,
        "slide_schema": None,
        "last_error": None,
        "planner_feedback": "",
        "slide_feedbacks": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_flow() -> None:
    for key in [
        "step",
        "selected_template",
        "user_input",
        "uploaded_data",
        "slide_schema",
        "last_error",
        "planner_feedback",
        "slide_feedbacks",
    ]:
        st.session_state.pop(key, None)


def go_to_step(step: int, *, clear_schema: bool = False) -> None:
    if clear_schema:
        st.session_state.slide_schema = None
        st.session_state.last_error = None
    st.session_state.step = step
    st.rerun()


def render_progress_bar(current_step: int) -> None:
    labels = ["1. 템플릿 선택", "2. 내용 입력", "3. 구조 확인", "4. 완료"]
    cols = st.columns(len(labels))
    for index, (col, label) in enumerate(zip(cols, labels), start=1):
        with col:
            if index < current_step:
                st.markdown(f"✅ ~~{label}~~")
            elif index == current_step:
                st.markdown(f"**▶ {label}**")
            else:
                st.markdown(label)
    st.divider()


def render_step_navigation() -> None:
    st.caption("단계 이동")
    cols = st.columns(4)
    steps = [(1, "템플릿"), (2, "내용 입력"), (3, "구조 확인"), (4, "완료")]
    for col, (step_no, label) in zip(cols, steps):
        with col:
            disabled = False
            if step_no == 2 and not st.session_state.selected_template:
                disabled = True
            if step_no >= 3 and not st.session_state.user_input:
                disabled = True
            if step_no == 4 and st.session_state.slide_schema is None:
                disabled = True
            if st.button(label, key=f"nav_{step_no}", use_container_width=True, disabled=disabled):
                go_to_step(step_no, clear_schema=step_no <= 2)


def parse_uploaded_file(uploaded_file: Any) -> dict[str, Any] | None:
    if uploaded_file is None:
        return None
    if uploaded_file.size and uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("업로드 파일은 10MB 이하만 지원합니다.")

    suffix = uploaded_file.name.rsplit(".", 1)[-1].lower()
    raw = uploaded_file.getvalue()

    if suffix == "json":
        payload = json.loads(raw.decode("utf-8"))
        if isinstance(payload, list) and payload:
            first = payload[0]
            columns = list(first.keys()) if isinstance(first, dict) else []
            rows = len(payload)
        elif isinstance(payload, dict):
            columns = list(payload.keys())
            rows = 1
        else:
            columns = []
            rows = 0
        return {"file_name": uploaded_file.name, "file_type": "json", "rows": rows, "columns": columns[:20]}

    if suffix == "csv":
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = reader.fieldnames or []
        rows = sum(1 for _ in reader)
        return {"file_name": uploaded_file.name, "file_type": "csv", "rows": rows, "columns": fieldnames[:20]}

    raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(SUPPORTED_UPLOAD_TYPES)}")


def build_user_request(user_input: dict[str, Any]) -> str:
    labels = {
        "period": "보고 기간",
        "done": "완료 업무",
        "plan": "다음 계획",
        "issues": "이슈 및 특이사항",
        "project_name": "프로젝트명",
        "goal": "프로젝트 목표",
        "progress": "진행 현황",
        "risks": "리스크 및 대응",
        "background": "배경 및 문제 정의",
        "solution": "핵심 제안 내용",
        "effect": "기대 효과",
        "resources": "필요 자원 및 실행 계획",
        "title": "분석 제목",
        "direction": "분석 방향",
        "reference_material": "참고용 긴 본문 또는 자료",
        "layout_preferences": "형태 및 배치 요구사항",
    }
    parts: list[str] = []
    for key, value in user_input.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        parts.append(f"[{labels.get(key, key)}]\n{value}")

    if st.session_state.planner_feedback.strip():
        parts.append(f"[구조 재생성 지시]\n{st.session_state.planner_feedback.strip()}")

    per_slide = []
    for slide_index in sorted(st.session_state.slide_feedbacks):
        feedback = st.session_state.slide_feedbacks[slide_index].strip()
        if feedback:
            per_slide.append(f"- 슬라이드 {slide_index}: {feedback}")
    if per_slide:
        parts.append("[슬라이드별 수정 지시]\n" + "\n".join(per_slide))

    return "\n\n".join(parts)


def get_layout_hint(slide: Slide) -> str:
    mapping = {
        "title": "상단 배너 + 중앙 제목 + 하단 발표자",
        "section": "좌측 컬러 패널 + 섹션 제목",
        "bullet": "상단 제목 + 본문 불릿 목록",
        "chart": "상단 제목 + 중앙 차트 영역",
        "table": "상단 제목 + 중앙 표 영역",
        "two_column": "상단 제목 + 좌우 2단 비교",
        "image": "상단 제목 + 중앙 이미지 영역",
        "blank": "빈 슬라이드",
    }
    return mapping.get(slide.type.value, slide.type.value)


def render_wireframe(slide: Slide) -> None:
    slide_type = slide.type.value
    if slide_type == "title":
        html = "<div style='border:1px solid #d9d9d9;border-radius:12px;background:#fff;height:220px;overflow:hidden'><div style='height:24%;background:#a50034'></div><div style='padding:20px 24px'><div style='height:28px;background:#ececec;border-radius:6px;width:72%;margin-bottom:16px'></div><div style='height:16px;background:#f2f2f2;border-radius:6px;width:48%;margin-bottom:50px'></div><div style='height:12px;background:#f2f2f2;border-radius:6px;width:22%;margin-left:auto'></div></div></div>"
    elif slide_type == "section":
        html = "<div style='display:flex;border:1px solid #d9d9d9;border-radius:12px;background:#fff;height:220px;overflow:hidden'><div style='width:34%;background:#a50034'></div><div style='flex:1;padding:28px'><div style='height:24px;background:#ececec;border-radius:6px;width:58%;margin-top:65px'></div></div></div>"
    elif slide_type == "two_column":
        html = "<div style='border:1px solid #d9d9d9;border-radius:12px;background:#fff;height:220px;padding:18px'><div style='height:20px;background:#ececec;border-radius:6px;width:34%;margin-bottom:18px'></div><div style='display:flex;height:150px'><div style='flex:1;background:#fafafa;border-radius:8px'></div><div style='width:8px'></div><div style='width:1px;background:#d9d9d9'></div><div style='width:8px'></div><div style='flex:1;background:#fafafa;border-radius:8px'></div></div></div>"
    else:
        html = "<div style='border:1px solid #d9d9d9;border-radius:12px;background:#fff;height:220px;padding:18px'><div style='height:20px;background:#ececec;border-radius:6px;width:34%;margin-bottom:18px'></div><div style='height:148px;background:#fafafa;border-radius:10px'></div></div>"
    st.markdown(html, unsafe_allow_html=True)


def render_step_1() -> None:
    st.title("어떤 내부 발표 자료를 만들까요?")
    st.caption("현재 MVP는 회사 전용 보고/기획 템플릿 생성을 우선 지원합니다.")

    cols = st.columns(2)
    for index, template in enumerate(TEMPLATES):
        with cols[index % 2]:
            selected = st.session_state.selected_template == template["id"]
            if st.button(f"{template['icon']} {template['name']}", key=f"template_{template['id']}", type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.selected_template = template["id"]
                st.rerun()

    _, right = st.columns([3, 1])
    with right:
        if st.button("다음 >", type="primary", use_container_width=True):
            if not st.session_state.selected_template:
                st.error("템플릿을 먼저 선택해주세요.")
            else:
                go_to_step(2)


def render_common_brief_inputs(inputs: dict[str, Any]) -> None:
    st.subheader("추가 브리프")
    st.caption("긴 본문이나 세부 오더가 많을수록 여기에서 충분히 설명해주세요.")
    inputs["reference_material"] = st.text_area(
        "참고할 긴 본문 / 회의 메모 / 복붙할 재료",
        height=220,
        value=st.session_state.user_input.get("reference_material", ""),
        placeholder="예: 회의록 전문, 메일 요약, 기존 보고서 본문, 반드시 들어가야 하는 문장 등",
    )
    inputs["layout_preferences"] = st.text_area(
        "원하는 형태 / 배치 / 강조 방식",
        height=140,
        value=st.session_state.user_input.get("layout_preferences", ""),
        placeholder="예: 2페이지는 좌우 비교형, 3페이지는 핵심 수치만 크게, 마지막은 일정표 형태",
    )


def render_step_2() -> None:
    template = st.session_state.selected_template
    st.title("내용을 입력해주세요")
    st.caption(f"선택한 템플릿: {TEMPLATE_NAMES.get(template, template)}")

    inputs: dict[str, Any] = {}
    left, right = st.columns([1.2, 1])

    with left:
        if template == "weekly_report":
            inputs["period"] = st.text_input("보고 기간 *", value=st.session_state.user_input.get("period", ""), placeholder="예: 2026년 4월 1주차")
            inputs["done"] = st.text_area(
                "이번 기간 주요 업무 *",
                value=st.session_state.user_input.get("done", ""),
                height=160,
                placeholder="예:\n- VoC 대시보드 구조 정리\n- 발표자료 초안 작성\n- 내부 검토 의견 반영",
            )
            inputs["plan"] = st.text_area(
                "다음 기간 계획 *",
                value=st.session_state.user_input.get("plan", ""),
                height=140,
                placeholder="예:\n- UI 수정안 반영\n- 템플릿 고도화\n- 사용자 피드백 수집",
            )
            inputs["issues"] = st.text_area(
                "이슈 / 특이사항",
                value=st.session_state.user_input.get("issues", ""),
                height=120,
                placeholder="예: API 비용 이슈, 브랜드 템플릿 원본 부재, 일정 지연 가능성",
            )
            required = ["period", "done", "plan"]
        elif template == "project_status":
            inputs["project_name"] = st.text_input("프로젝트명 *", value=st.session_state.user_input.get("project_name", ""), placeholder="예: PPTAgent")
            inputs["period"] = st.text_input("프로젝트 기간 *", value=st.session_state.user_input.get("period", ""), placeholder="예: 2026.04 ~ 2026.06")
            inputs["goal"] = st.text_area(
                "프로젝트 목표 *",
                value=st.session_state.user_input.get("goal", ""),
                height=120,
                placeholder="예: 회사 내부 발표자료 제작 시간을 줄이는 AI Agent MVP 구축",
            )
            inputs["progress"] = st.text_area(
                "현재 진행 현황 *",
                value=st.session_state.user_input.get("progress", ""),
                height=160,
                placeholder="예:\n- Step 기반 UI 연결 완료\n- OpenAI 연동 전환 진행 중\n- 렌더러 회사 전용 테마 반영",
            )
            inputs["risks"] = st.text_area(
                "리스크 / 대응 계획",
                value=st.session_state.user_input.get("risks", ""),
                height=120,
                placeholder="예: API 크레딧 부족 가능성, 실제 사용자 요구 반영 필요",
            )
            required = ["project_name", "period", "goal", "progress"]
        elif template == "proposal":
            inputs["background"] = st.text_area(
                "제안 배경 / 문제 정의 *",
                value=st.session_state.user_input.get("background", ""),
                height=140,
                placeholder="예: 내부 보고자료 작성에 반복 작업이 많고 형식 정리가 오래 걸림",
            )
            inputs["solution"] = st.text_area(
                "핵심 제안 내용 *",
                value=st.session_state.user_input.get("solution", ""),
                height=160,
                placeholder="예: 템플릿 기반 AI PPT 생성 도구를 도입해 기획부터 초안까지 자동화",
            )
            inputs["effect"] = st.text_area(
                "기대 효과 *",
                value=st.session_state.user_input.get("effect", ""),
                height=120,
                placeholder="예: 문서 작성 시간 단축, 보고 품질 표준화, 협업 속도 향상",
            )
            inputs["resources"] = st.text_area(
                "필요 자원 / 실행 계획",
                value=st.session_state.user_input.get("resources", ""),
                height=100,
                placeholder="예: 2주 MVP 개발, 디자인 검토 1회, 실사용자 파일 샘플 확보",
            )
            required = ["background", "solution", "effect"]
        elif template == "data_report":
            inputs["title"] = st.text_input("분석 제목 *", value=st.session_state.user_input.get("title", ""), placeholder="예: 2026 Q1 고객 VOC 분석 결과")
            inputs["background"] = st.text_area(
                "분석 배경 및 목적 *",
                value=st.session_state.user_input.get("background", ""),
                height=120,
                placeholder="예: 최근 3개월 VOC를 요약해 주요 이슈와 개선 우선순위를 보고",
            )
            uploaded = st.file_uploader("데이터 파일 업로드 (CSV / JSON)", type=list(SUPPORTED_UPLOAD_TYPES))
            if uploaded:
                try:
                    uploaded_summary = parse_uploaded_file(uploaded)
                    st.session_state.uploaded_data = uploaded_summary
                    inputs["uploaded_file_name"] = uploaded.name
                    st.success(f"{uploaded.name} 업로드 완료 | 행 수: {uploaded_summary['rows']} | 컬럼: {', '.join(uploaded_summary['columns']) or '없음'}")
                except Exception as exc:
                    st.session_state.uploaded_data = None
                    st.error(f"파일을 읽지 못했습니다: {exc}")
            inputs["direction"] = st.text_area(
                "분석 방향 / 보고 포인트",
                value=st.session_state.user_input.get("direction", ""),
                height=120,
                placeholder="예: 불만 유형 Top 3, 월별 추이, 즉시 조치 가능한 개선안 중심으로 정리",
            )
            required = ["title", "background"]
        else:
            st.error("지원하지 않는 템플릿입니다.")
            required = []

    with right:
        render_common_brief_inputs(inputs)
        st.info(
            "팁: 긴 본문을 다 넣어도 됩니다.\n\n- 꼭 들어갈 문장\n- 페이지별 원하는 형태\n- 강조해야 할 수치\n- 특정 페이지 위치 요구\n\n같은 내용을 자세히 적어두면 Step 3에서 더 정교하게 다듬기 쉽습니다."
        )

    left_btn, mid_btn, right_btn = st.columns([1, 1.4, 1])
    with left_btn:
        if st.button("< 템플릿으로", use_container_width=True):
            go_to_step(1, clear_schema=True)
    with mid_btn:
        if st.button("입력 내용 임시 저장", use_container_width=True):
            st.session_state.user_input = inputs
            st.success("현재 입력 내용을 유지했습니다.")
    with right_btn:
        if st.button("구조 생성으로 >", type="primary", use_container_width=True):
            missing = [field for field in required if not str(inputs.get(field, "")).strip()]
            if missing:
                st.error("필수 입력 항목을 모두 채워주세요.")
            else:
                st.session_state.user_input = inputs
                st.session_state.slide_schema = None
                st.session_state.last_error = None
                go_to_step(3)


def render_step_3() -> None:
    st.title("슬라이드 구조를 확인해주세요")
    st.caption("구조를 먼저 만들고, 각 슬라이드에 구체적인 수정 지시를 추가로 줄 수 있습니다.")

    if st.session_state.slide_schema is None:
        with st.spinner("슬라이드 구조를 기획하는 중입니다..."):
            try:
                llm = get_default_llm()
                schema = llm.plan_slides(build_user_request(st.session_state.user_input), str(st.session_state.selected_template), st.session_state.uploaded_data)
                st.session_state.slide_schema = schema
                st.session_state.last_error = None
                st.rerun()
            except Exception as exc:
                logger.exception("Failed to plan slides")
                st.session_state.last_error = str(exc)

    if st.session_state.slide_schema is None:
        st.error(st.session_state.last_error or "슬라이드 구조 생성에 실패했습니다. 잠시 후 다시 시도해주세요.")
        st.warning("현재 OpenAI 키는 형식상 정상으로 보이지만, 테스트 결과 `insufficient_quota`가 반환되었습니다. OpenAI 플랫폼의 결제/크레딧 상태를 확인해주세요.")
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as handle:
                env_text = handle.read()
            if "your_openai_api_key_here" in env_text:
                st.info("현재 .env에 예시 API 키가 들어 있습니다. 실제 OpenAI API 키로 바꿔야 Step 3이 동작합니다.")

        nav_left, nav_mid, nav_right = st.columns([1, 1, 1])
        with nav_left:
            if st.button("< 내용 입력으로", use_container_width=True):
                go_to_step(2)
        with nav_mid:
            if st.button("< 템플릿 선택으로", use_container_width=True):
                go_to_step(1, clear_schema=True)
        with nav_right:
            if st.button("다시 시도", use_container_width=True):
                st.session_state.slide_schema = None
                st.session_state.last_error = None
                st.rerun()
        return

    schema: SlideSchema = st.session_state.slide_schema
    st.success(f"총 {len(schema.slides)}장의 슬라이드 구성이 준비되었습니다.")
    st.subheader("전체 구조 피드백")
    st.session_state.planner_feedback = st.text_area(
        "구조 재생성 지시",
        value=st.session_state.planner_feedback,
        height=120,
        placeholder="예: 3페이지는 표 대신 좌우 비교형으로, 마지막 페이지는 실행 일정으로 바꿔줘",
    )

    for slide in schema.slides:
        title = slide.content.title or slide.content.heading or "(제목 없음)"
        with st.container(border=True):
            left, right = st.columns([1, 1.2])
            with left:
                st.markdown(f"**{slide.index}. {title}**")
                st.caption(f"타입: `{slide.type.value}` | 기본 레이아웃: {get_layout_hint(slide)}")
                render_wireframe(slide)
            with right:
                st.markdown("**현재 내용 요약**")
                if slide.content.points:
                    for point in slide.content.points[:5]:
                        st.write(f"- {point}")
                else:
                    compact = []
                    for field in ["subtitle", "presenter", "notes", "left_title", "right_title"]:
                        value = getattr(slide.content, field, None)
                        if value:
                            compact.append(f"- {field}: {value}")
                    st.write("\n".join(compact) if compact else "요약 가능한 본문이 아직 많지 않습니다.")

                st.session_state.slide_feedbacks[slide.index] = st.text_area(
                    "이 슬라이드에 대한 구체적 오더",
                    key=f"slide_feedback_{slide.index}",
                    value=st.session_state.slide_feedbacks.get(slide.index, ""),
                    height=100,
                    placeholder="예: 제목은 더 짧게, 좌측에는 배경 / 우측에는 기대효과, 숫자는 크게 강조",
                )

    left_btn, mid_btn, right_btn = st.columns([1, 1.4, 1])
    with left_btn:
        if st.button("< 내용 입력 수정", use_container_width=True):
            go_to_step(2)
    with mid_btn:
        if st.button("이 피드백으로 구조 다시 생성", use_container_width=True):
            st.session_state.slide_schema = None
            st.session_state.last_error = None
            st.rerun()
    with right_btn:
        if st.button("PPT 생성으로 >", type="primary", use_container_width=True):
            go_to_step(4)


def render_step_4() -> None:
    st.title("발표 자료가 준비되었습니다")
    schema: SlideSchema | None = st.session_state.slide_schema
    if schema is None:
        st.error("생성할 슬라이드 구조가 없습니다. 이전 단계로 돌아가 다시 시도해주세요.")
        left, right = st.columns(2)
        with left:
            if st.button("< 구조 확인으로", use_container_width=True):
                go_to_step(3)
        with right:
            if st.button("< 내용 입력으로", use_container_width=True):
                go_to_step(2)
        return

    with st.spinner("발표 자료 파일을 생성하는 중입니다..."):
        try:
            pptx_bytes = render_pptx(schema)
        except Exception as exc:
            logger.exception("Failed to render PPTX")
            st.error(f"PPTX 파일 생성에 실패했습니다. 잠시 후 다시 시도해주세요.\n\n오류: {exc}")
            left, right = st.columns(2)
            with left:
                if st.button("< 구조 확인으로", use_container_width=True):
                    go_to_step(3)
            with right:
                if st.button("< 내용 입력으로", use_container_width=True):
                    go_to_step(2)
            return

    safe_title = re.sub(r'[\\/:*?"<>|]+', "_", str(schema.meta.title or "PPTAgent"))
    st.download_button(
        label="PPTX 다운로드",
        data=pptx_bytes,
        file_name=f"{safe_title}.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary",
        use_container_width=True,
    )

    left, right = st.columns(2)
    with left:
        if st.button("< 구조 다시 보기", use_container_width=True):
            go_to_step(3)
    with right:
        if st.button("새 발표 자료 만들기", use_container_width=True):
            reset_flow()
            st.rerun()


def main() -> None:
    init_session()
    render_progress_bar(int(st.session_state.step))
    render_step_navigation()
    step = st.session_state.step
    if step == 1:
        render_step_1()
    elif step == 2:
        render_step_2()
    elif step == 3:
        render_step_3()
    elif step == 4:
        render_step_4()
    else:
        reset_flow()
        st.rerun()


if __name__ == "__main__":
    main()