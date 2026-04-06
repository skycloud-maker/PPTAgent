"""LG-style Streamlit studio for PPTAgent."""

from __future__ import annotations

import html
import logging
import os
import re
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from core.llm import get_default_llm
from core.renderer import render_pptx
from core.schema import Slide, SlideContent, SlideMeta, SlideSchema, SlideType
from core.template_packs import TemplatePack, get_template_pack, list_template_packs

load_dotenv()

logger = logging.getLogger(__name__)

st.set_page_config(page_title="PPTAgent Studio", page_icon="P", layout="wide")

COMPANY_NAME = os.getenv("PPTAGENT_COMPANY_NAME", "LG Electronics")
CONFIDENTIAL_LABEL = os.getenv("PPTAGENT_CONFIDENTIAL_LABEL", "LGE Internal Use Only")

COMMON_FIELDS = {
    "department": ("부서 / 조직", "예: HS본부 고객가치혁신실"),
    "role": ("작성자 역할", "예: 책임 / 파트장 / PM"),
    "audience": ("보고 대상", "예: 임원 / 조직장 / 유관부서장"),
    "objective": ("이번 보고 목적", "예: 이번 주 성과 공유와 다음 주 지원 요청"),
    "reference_material": ("참고할 긴 본문 / 회의 메모 / 복붙 재료", "예: 회의 메모, 기존 보고서 문장, 이메일 초안 등을 길게 넣어주세요."),
    "layout_preferences": ("원하는 형태 / 배치 / 강조 방식", "예: 2페이지는 핵심 요약, 3페이지는 표, 마지막은 요청사항 중심"),
}

PACK_FIELDS = {
    "weekly_exec": [
        ("period", "보고 기간 *", "예: 2026년 4월 1주차 (03.30 ~ 04.05)"),
        ("done", "?? ?? *", "?:\n- PPTAgent MVP ?? ?? ?? ??\n- Streamlit ??? UI ??\n- LG ??? ??? ??"),
        ("plan", "?? ?? *", "?:\n- OpenAI ?? ?? ???\n- ?? ?? ??? ??\n- ??? ?? ??"),
        ("issues", "?? / ????", "?:\n- API ?? ?? ??\n- ?? ?? ?? ?? ?? ?? ??"),
    ],
    "project_exec": [
        ("project_name", "????? *", "?: PPTAgent"),
        ("goal", "???? ?? *", "?:\n- ?? ???? ??\n- ??? ?? ?? ???"),
        ("progress", "?? ?? *", "?:\n- UI ?? ??\n- ??? ??? ??\n- ??? ?? ?? ??"),
        ("risks", "??? / ????", "?:\n- ?? ?? ?? ??\n- ??/?? ?? ??"),
    ],
    "proposal_exec": [
        ("background", "?? ? ?? ?? *", "?:\n- ?? ?? ??? ?? ?? ?\n- ?? ?? ??? ?"),
        ("solution", "?? ?? *", "?:\n- ?? ?? ??? ??? + AI ?? Agent"),
        ("effect", "?? ?? *", "?:\n- ?? ?? ??\n- ?? ?? ?? ??"),
        ("resources", "?? ?? / ?? ??", "?:\n- MVP ???\n- ??? ?? ??\n- ?? ??"),
    ],
}

THEME_PRESETS = {
    "LGE Core": {"primary": "#A50034", "secondary": "#2C3142", "accent": "#D9DEE8", "text": "#202532", "muted": "#6B7280", "surface": "#F7F8FB", "background": "#FFFFFF", "support": "#0E7A53", "border": "#D9DEE6"},
    "LGE Executive": {"primary": "#A50034", "secondary": "#4D5566", "accent": "#E9ECF2", "text": "#1F2937", "muted": "#7B8394", "surface": "#FBFBFC", "background": "#FFFFFF", "support": "#1B7F6B", "border": "#E3E7EE"},
    "LGE Data": {"primary": "#A50034", "secondary": "#1E3A5F", "accent": "#E8EDF6", "text": "#18212F", "muted": "#667085", "surface": "#F5F7FA", "background": "#FFFFFF", "support": "#0E7A53", "border": "#D6DCE6"},
}

COLOR_FIELDS = [("primary", "대표색"), ("secondary", "보조색"), ("accent", "강조색"), ("background", "배경"), ("surface", "카드 배경"), ("text", "본문"), ("muted", "보조 텍스트"), ("support", "보조 포인트"), ("border", "라인")]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f6f7fa 0%, #eef1f5 100%); }
        .block-container { max-width: none; padding-top: 1rem; padding-bottom: 2.5rem; padding-left: 18px; padding-right: 18px; }
        .lg-shell { background: rgba(255,255,255,.92); border: 1px solid #dde2ea; border-radius: 28px; box-shadow: 0 16px 48px rgba(17,24,39,.06); overflow: hidden; margin-bottom: 1rem; }
        .lg-topline { height: 6px; background: #a50034; }
        .lg-header { padding: 18px 28px 20px; background: linear-gradient(180deg, #ffffff 0%, #fbfbfd 100%); }
        .lg-eyebrow { font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: #7b8394; margin-bottom: .45rem; }
        .lg-title { font-size: 2.05rem; font-weight: 800; color: #202532; margin-bottom: .35rem; }
        .lg-copy { font-size: .95rem; line-height: 1.65; color: #596273; max-width: 1050px; }
        .panel { background: rgba(255,255,255,.96); border: 1px solid #dde2ea; border-radius: 24px; padding: 18px; box-shadow: 0 10px 26px rgba(17,24,39,.04); margin-bottom: 1rem; }
        .panel-title { font-size: 1.02rem; font-weight: 800; color: #202532; margin-bottom: .2rem; }
        .panel-copy { font-size: .88rem; line-height: 1.6; color: #6b7280; margin-bottom: .9rem; }
        .kicker { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; background: #f8ebf0; color: #a50034; font-size: .75rem; font-weight: 700; margin-bottom: .6rem; }
        .metric { border: 1px solid #e3e7ee; border-radius: 18px; padding: 12px 14px; background: #fbfbfc; margin-bottom: .7rem; }
        .metric-label { font-size: .74rem; color: #7b8394; text-transform: uppercase; letter-spacing: .06em; }
        .metric-value { font-size: 1.08rem; font-weight: 800; color: #202532; margin-top: .18rem; }
        .pack-card { border: 1px solid #dfe4ec; border-radius: 22px; background: linear-gradient(180deg, #fff 0%, #fbfbfc 100%); padding: 18px; height: 100%; }
        .pack-card-top { height: 4px; border-radius: 999px; background: #a50034; margin-bottom: 14px; }
        .preview-frame { background: #eef1f5; border: 1px solid #dde2ea; border-radius: 26px; padding: 18px; overflow: hidden; min-height: 720px; }
        .slide-meta { display: inline-flex; padding: 6px 12px; border-radius: 999px; background: #f3f4f6; color: #4b5563; font-size: .76rem; font-weight: 700; margin-bottom: .75rem; }
        .helper { font-size: .82rem; line-height: 1.6; color: #6b7280; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "step": 1,
        "selected_pack_id": "weekly_exec",
        "brief": {},
        "slide_schema": None,
        "selected_slide_idx": 1,
        "selected_block": "All Slide",
        "block_instruction": "",
        "theme_preset": "LGE Core",
        "theme": dict(THEME_PRESETS["LGE Core"]),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_step(step: int) -> None:
    st.session_state.step = step
    st.rerun()


def current_theme() -> dict[str, str]:
    theme = dict(THEME_PRESETS["LGE Core"])
    theme.update(st.session_state.get("theme", {}))
    return theme


def sync_theme_from_preset() -> None:
    st.session_state.theme = dict(THEME_PRESETS.get(st.session_state.get("theme_preset", "LGE Core"), THEME_PRESETS["LGE Core"]))

def build_request(pack: TemplatePack) -> str:
    lines = [f"[template_pack]\n{pack.name}"]
    for key, value in st.session_state.brief.items():
        value_str = str(value).strip()
        if value_str:
            lines.append(f"[{key}]\n{value_str}")
    for slide in get_schema(pack).slides:
        feedback_key = f"slide_feedback_{slide.index}"
        feedback = str(st.session_state.get(feedback_key, "")).strip()
        if feedback:
            lines.append(f"[slide_{slide.index}_feedback]\n{feedback}")
    lines.append(f"[theme]\n{current_theme()}")
    return "\n\n".join(lines)


def bootstrap_schema(pack: TemplatePack) -> SlideSchema:
    slides = []
    for idx, blueprint in enumerate(pack.slides, start=1):
        content = SlideContent(
            heading=blueprint.title,
            title=blueprint.title,
            subtitle=blueprint.objective if idx == 1 else None,
            caption=blueprint.guidance if idx == 1 else None,
            points=[blueprint.objective, blueprint.guidance],
            notes=blueprint.guidance,
            left_title="Plan",
            right_title="Risk / Support",
            left_points=["Key item 1", "Key item 2"],
            right_points=["Support item 1", "Risk item 2"],
            data={"headers": ["Category", "Main Point", "Meaning"], "rows": [["Item", blueprint.objective, "Meaning"]], "categories": ["Plan", "Build", "Test", "Share"], "series": [{"name": "Progress", "values": [35, 55, 72, 88]}]},
        )
        slides.append(Slide(index=idx, type=SlideType(blueprint.type), content=content))
    return SlideSchema(meta=SlideMeta(title=pack.name, template=pack.id, language="ko", total_slides=len(slides)), slides=slides)


def get_schema(pack: TemplatePack) -> SlideSchema:
    schema = st.session_state.slide_schema
    if isinstance(schema, SlideSchema) and schema.slides:
        for idx, slide in enumerate(schema.slides, start=1):
            slide.index = idx
        schema.meta.total_slides = len(schema.slides)
        return schema
    schema = bootstrap_schema(pack)
    st.session_state.slide_schema = schema
    return schema


def table_to_text(data: dict[str, Any] | None) -> str:
    data = data or {}
    headers = data.get("headers") or ["Category", "Main Point", "Meaning"]
    rows = data.get("rows") or []
    lines = [" | ".join(str(item) for item in headers)]
    for row in rows:
        lines.append(" | ".join(str(item) for item in row))
    return "\n".join(lines)


def chart_to_text(data: dict[str, Any] | None) -> str:
    data = data or {}
    categories = data.get("categories") or ["Plan", "Build", "Test", "Share"]
    series = data.get("series") or [{"name": "Progress", "values": [40, 60, 75, 88]}]
    if not series:
        return ""
    return f"categories: {', '.join(str(item) for item in categories)}\nvalues: {', '.join(str(v) for v in series[0].get('values', []))}"


def ensure_slide_state(slide: Slide) -> None:
    prefix = f"slide_{slide.index}"
    defaults = {
        f"{prefix}_type": slide.type.value,
        f"{prefix}_title": slide.content.title or slide.content.heading or "",
        f"{prefix}_points": "\n".join(slide.content.points or []),
        f"{prefix}_notes": slide.content.notes or "",
        f"{prefix}_left_title": slide.content.left_title or "Plan",
        f"{prefix}_right_title": slide.content.right_title or "Risk / Support",
        f"{prefix}_left_points": "\n".join(slide.content.left_points or []),
        f"{prefix}_right_points": "\n".join(slide.content.right_points or []),
        f"{prefix}_table": table_to_text(slide.content.data),
        f"{prefix}_chart": chart_to_text(slide.content.data),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def parse_lines(text: str) -> list[str]:
    return [line.strip().lstrip('-? ') for line in text.splitlines() if line.strip().lstrip('-? ')]


def parse_table_text(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"headers": ["Category", "Main Point", "Meaning"], "rows": []}
    headers = [item.strip() for item in lines[0].split("|")]
    rows = [[item.strip() for item in line.split("|")] for line in lines[1:]]
    return {"headers": headers, "rows": rows}


def parse_chart_text(text: str) -> dict[str, Any]:
    categories = ["Plan", "Build", "Test", "Share"]
    values = [40, 60, 75, 88]
    for line in text.splitlines():
        lower = line.lower().strip()
        if lower.startswith("categories:"):
            categories = [item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()]
        if lower.startswith("values:"):
            parsed = []
            for item in [item.strip() for item in line.split(":", 1)[1].split(",") if item.strip()]:
                try:
                    parsed.append(int(float(item)))
                except ValueError:
                    pass
            if parsed:
                values = parsed
    return {"categories": categories, "series": [{"name": "Progress", "values": values}]}


def apply_manual_edits(schema: SlideSchema) -> SlideSchema:
    for idx, slide in enumerate(schema.slides, start=1):
        slide.index = idx
        ensure_slide_state(slide)
        prefix = f"slide_{slide.index}"
        slide.type = SlideType(st.session_state.get(f"{prefix}_type", slide.type.value))
        title = str(st.session_state.get(f"{prefix}_title", "")).strip()
        points = parse_lines(str(st.session_state.get(f"{prefix}_points", "")))
        notes = str(st.session_state.get(f"{prefix}_notes", "")).strip()
        slide.content.title = title
        slide.content.heading = title
        slide.content.points = points
        slide.content.notes = notes
        if slide.type == SlideType.TITLE:
            slide.content.subtitle = points[0] if points else slide.content.subtitle
            slide.content.caption = notes or slide.content.caption
        if slide.type == SlideType.TWO_COLUMN:
            slide.content.left_title = str(st.session_state.get(f"{prefix}_left_title", "Plan")).strip() or "Plan"
            slide.content.right_title = str(st.session_state.get(f"{prefix}_right_title", "Risk / Support")).strip() or "Risk / Support"
            slide.content.left_points = parse_lines(str(st.session_state.get(f"{prefix}_left_points", "")))
            slide.content.right_points = parse_lines(str(st.session_state.get(f"{prefix}_right_points", "")))
        if slide.type == SlideType.TABLE:
            slide.content.data = parse_table_text(str(st.session_state.get(f"{prefix}_table", "")))
        if slide.type == SlideType.CHART:
            slide.content.data = parse_chart_text(str(st.session_state.get(f"{prefix}_chart", "")))
    schema.meta.total_slides = len(schema.slides)
    st.session_state.slide_schema = schema
    return schema


def block_options(slide: Slide) -> list[str]:
    if slide.type == SlideType.TITLE:
        return ["All Slide", "Title", "Subtitle", "Message"]
    if slide.type == SlideType.TABLE:
        return ["All Slide", "Title", "Table", "Summary"]
    if slide.type == SlideType.CHART:
        return ["All Slide", "Title", "Chart", "Insight"]
    if slide.type == SlideType.TWO_COLUMN:
        return ["All Slide", "Title", "Left Column", "Right Column"]
    return ["All Slide", "Title", "Message", "Secondary"]


def highlight_style(name: str, selected: str, color: str) -> str:
    return f"box-shadow: inset 0 0 0 2px {color};" if name == selected else ""

def preview_html(slide: Slide, theme: dict[str, str], selected_block: str) -> str:
    primary = theme["primary"]
    secondary = theme["secondary"]
    text = theme["text"]
    muted = theme["muted"]
    surface = theme["surface"]
    background = theme["background"]
    border = theme["border"]

    def esc(value: str | None, fallback: str = "") -> str:
        return html.escape(value or fallback)

    title = esc(slide.content.title or slide.content.heading, "Slide Title")
    if slide.type == SlideType.TITLE:
        points = "".join(f"<li style='margin-bottom:10px'>{esc(point)}</li>" for point in (slide.content.points or [])[:3])
        return f"""
        <div style='position:relative;background:{background};border:1px solid {border};border-radius:18px;aspect-ratio:16/9;padding:26px 34px;overflow:hidden'>
          <div style='position:absolute;left:0;top:0;width:100%;height:6px;background:{primary}'></div>
          <div style='position:absolute;left:0;top:64px;width:14px;height:112px;background:{primary}'></div>
          <div style='position:absolute;left:0;top:168px;width:64px;height:12px;background:{primary}'></div>
          <div style='position:absolute;right:0;bottom:0;width:120px;height:12px;background:{primary}'></div>
          <div style='position:absolute;left:50%;top:18px;transform:translateX(-50%);font-size:11px;color:{muted};font-family:Arial Narrow'>{esc(CONFIDENTIAL_LABEL)}</div>
          <div style='font-size:12px;color:{primary};font-weight:700;line-height:1.7;{highlight_style("Secondary", selected_block, primary)}'>{esc(slide.content.caption, 'Internal executive reporting deck')}</div>
          <div style='margin-top:72px;font-size:42px;font-weight:800;line-height:1.18;color:{secondary};{highlight_style("Title", selected_block, primary)}'>{title}</div>
          <div style='margin-top:18px;font-size:18px;color:{text};{highlight_style("Subtitle", selected_block, primary)}'>{esc(slide.content.subtitle, 'Report title and key message')}</div>
          <div style='margin-top:28px;font-size:15px;color:{text};{highlight_style("Message", selected_block, primary)}'><ul style='padding-left:24px;margin:0'>{points}</ul></div>
          <div style='position:absolute;left:78px;bottom:38px;font-size:13px;font-weight:700;color:{secondary}'>{esc(COMPANY_NAME)}</div>
          <div style='position:absolute;left:50%;bottom:10px;transform:translateX(-50%);font-size:10px;font-weight:700;color:{primary};font-family:Arial Narrow'>| CONFIDENTIAL |</div>
        </div>
        """
    if slide.type == SlideType.TABLE:
        data = slide.content.data or {}
        headers = data.get("headers") or ["Category", "Main Point", "Meaning"]
        rows = data.get("rows") or [["Item", "Content", "Meaning"]]
        head = "".join(f"<div style='padding:11px 12px;background:#eef1f5;font-weight:700;font-size:13px;color:{secondary}'>{esc(str(item))}</div>" for item in headers)
        body = ""
        for row in rows[:5]:
            cells = row + [""] * max(0, len(headers) - len(row))
            body += "".join(f"<div style='padding:12px;border-top:1px solid {border};font-size:12px;color:{text};background:{background}'>{esc(str(cell))}</div>" for cell in cells[:len(headers)])
        cols = " ".join(["1fr"] * len(headers))
        return f"<div style='position:relative;background:{background};border:1px solid {border};border-radius:18px;aspect-ratio:16/9;padding:22px 26px'><div style='position:absolute;left:50%;top:14px;transform:translateX(-50%);font-size:11px;color:{muted};font-family:Arial Narrow'>{esc(CONFIDENTIAL_LABEL)}</div><div style='margin-top:16px;font-size:29px;font-weight:800;color:{text};{highlight_style("Title", selected_block, primary)}'>{title}</div><div style='height:2px;background:{secondary};margin:8px 0 18px'></div><div style='display:grid;grid-template-columns:{cols};border:1px solid {border};border-radius:12px;overflow:hidden;{highlight_style("Table", selected_block, primary)}'>{head}{body}</div></div>"
    if slide.type == SlideType.TWO_COLUMN:
        left_points = "".join(f"<li style='margin-bottom:8px'>{esc(point)}</li>" for point in (slide.content.left_points or [])[:5])
        right_points = "".join(f"<li style='margin-bottom:8px'>{esc(point)}</li>" for point in (slide.content.right_points or [])[:5])
        return f"<div style='position:relative;background:{background};border:1px solid {border};border-radius:18px;aspect-ratio:16/9;padding:22px 26px'><div style='position:absolute;left:50%;top:14px;transform:translateX(-50%);font-size:11px;color:{muted};font-family:Arial Narrow'>{esc(CONFIDENTIAL_LABEL)}</div><div style='margin-top:16px;font-size:29px;font-weight:800;color:{text};{highlight_style("Title", selected_block, primary)}'>{title}</div><div style='height:2px;background:{secondary};margin:8px 0 18px'></div><div style='display:grid;grid-template-columns:1fr 1fr;gap:18px'><div style='border:1px solid {border};border-radius:14px;padding:16px;background:{background};{highlight_style("Left Column", selected_block, primary)}'><div style='font-size:15px;font-weight:800;color:{primary};margin-bottom:10px'>{esc(slide.content.left_title, 'Left')}</div><ul style='padding-left:20px;margin:0;color:{text};font-size:13px;line-height:1.65'>{left_points}</ul></div><div style='border:1px solid {border};border-radius:14px;padding:16px;background:{surface};{highlight_style("Right Column", selected_block, primary)}'><div style='font-size:15px;font-weight:800;color:{primary};margin-bottom:10px'>{esc(slide.content.right_title, 'Right')}</div><ul style='padding-left:20px;margin:0;color:{text};font-size:13px;line-height:1.65'>{right_points}</ul></div></div></div>"
    if slide.type == SlideType.CHART:
        data = slide.content.data or {}
        categories = data.get("categories") or ["Plan", "Build", "Test", "Share"]
        values = (data.get("series") or [{"values": [40, 60, 75, 88]}])[0].get("values") or [40, 60, 75, 88]
        bars = "".join(f"<div style='display:flex;flex-direction:column;align-items:center;gap:8px'><div style='width:54px;height:{max(28, int(v)*2)}px;background:{primary if i % 2 else secondary};border-radius:10px 10px 0 0'></div><div style='font-size:12px;color:{muted}'>{esc(str(categories[i]))}</div></div>" for i, v in enumerate(values[: min(len(categories), len(values), 4)]))
        insights = "".join(f"<li style='margin-bottom:8px'>{esc(point)}</li>" for point in (slide.content.points or [])[:4])
        return f"<div style='position:relative;background:{background};border:1px solid {border};border-radius:18px;aspect-ratio:16/9;padding:22px 26px'><div style='position:absolute;left:50%;top:14px;transform:translateX(-50%);font-size:11px;color:{muted};font-family:Arial Narrow'>{esc(CONFIDENTIAL_LABEL)}</div><div style='margin-top:16px;font-size:29px;font-weight:800;color:{text};{highlight_style("Title", selected_block, primary)}'>{title}</div><div style='height:2px;background:{secondary};margin:8px 0 18px'></div><div style='display:grid;grid-template-columns:1.35fr .9fr;gap:18px'><div style='border:1px solid {border};border-radius:14px;padding:20px;background:{background};{highlight_style("Chart", selected_block, primary)}'><div style='display:flex;align-items:end;justify-content:space-around;min-height:230px'>{bars}</div></div><div style='border:1px solid {border};border-radius:14px;padding:16px;background:{surface};{highlight_style("Insight", selected_block, primary)}'><div style='font-size:15px;font-weight:800;color:{primary};margin-bottom:10px'>Insights</div><ul style='padding-left:20px;margin:0;color:{text};font-size:13px;line-height:1.65'>{insights}</ul></div></div></div>"
    points = "".join(f"<li style='margin-bottom:10px'>{esc(point)}</li>" for point in (slide.content.points or [])[:6])
    return f"<div style='position:relative;background:{background};border:1px solid {border};border-radius:18px;aspect-ratio:16/9;padding:22px 26px'><div style='position:absolute;left:50%;top:14px;transform:translateX(-50%);font-size:11px;color:{muted};font-family:Arial Narrow'>{esc(CONFIDENTIAL_LABEL)}</div><div style='margin-top:16px;font-size:29px;font-weight:800;color:{text};{highlight_style("Title", selected_block, primary)}'>{title}</div><div style='height:2px;background:{secondary};margin:8px 0 18px'></div><div style='border:1px solid {border};border-radius:14px;padding:18px;background:{surface};{highlight_style("Message", selected_block, primary)}'><ul style='padding-left:22px;margin:0;color:{text};font-size:14px;line-height:1.75'>{points}</ul></div></div>"


def pack_completion_ratio(pack: TemplatePack) -> str:
    required = len(pack.required_fields)
    if not required:
        return "100%"
    completed = sum(1 for key in pack.required_fields if str(st.session_state.brief.get(key, "")).strip())
    return f"{round((completed / required) * 100)}%"


def render_header(title: str, copy: str) -> None:
    st.markdown(f"<div class='lg-shell'><div class='lg-topline'></div><div class='lg-header'><div class='lg-eyebrow'>{html.escape(CONFIDENTIAL_LABEL)}</div><div class='lg-title'>{html.escape(title)}</div><div class='lg-copy'>{html.escape(copy)}</div></div></div>", unsafe_allow_html=True)

def render_pack_picker() -> None:
    render_header("PPTAgent Studio", "LG 내부 보고 템플릿 위에서 구조는 안정적으로 유지하고, 생성형 AI가 문구와 배치를 보정하는 작업 공간입니다.")
    st.title("보고 템플릿 팩 선택")
    st.caption("업무 성격에 맞는 보고 팩을 고르면, 그 구조 안에서 내용만 빠르게 채워 고품질 보고서를 만들 수 있습니다.")
    cols = st.columns(3, gap="large")
    for idx, pack in enumerate(list_template_packs()):
        with cols[idx % 3]:
            st.markdown("<div class='pack-card'><div class='pack-card-top'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kicker'>{pack.icon} {pack.name}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='panel-copy'>{pack.summary}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='helper'><strong>추천 상황</strong><br>{pack.recommended_for}</div>", unsafe_allow_html=True)
            if st.button("이 팩으로 시작", key=f"pick_pack_{pack.id}", use_container_width=True, type="primary" if st.session_state.selected_pack_id == pack.id else "secondary", help="선택한 보고 구조를 작업 화면에 불러옵니다."):
                st.session_state.selected_pack_id = pack.id
                st.session_state.slide_schema = bootstrap_schema(pack)
                st.session_state.selected_slide_idx = 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    _, right = st.columns([4, 1])
    with right:
        if st.button("작업실 열기 >", key="goto_studio", use_container_width=True, type="primary", help="선택한 템플릿 팩으로 편집 화면으로 이동합니다."):
            go_to_step(2)


def render_studio() -> None:
    pack = get_template_pack(st.session_state.selected_pack_id)
    schema = apply_manual_edits(get_schema(pack))
    selected_idx = min(max(1, st.session_state.selected_slide_idx), len(schema.slides))
    st.session_state.selected_slide_idx = selected_idx
    selected_slide = schema.slides[selected_idx - 1]
    ensure_slide_state(selected_slide)

    render_header(
        "AI Studio",
        "브리프 입력, 실시간 미리보기, 선택 영역 AI 수정, 테마 조정까지 한 화면에서 처리합니다. 실제 PPT 비율에 가깝게 보면서 편집할 수 있도록 미리보기를 강화했습니다.",
    )

    t1, t2, t3, t4 = st.columns(4, gap="small")
    with t1:
        if st.button("AI 초안 생성 / 새로고침", key="toolbar_generate", use_container_width=True, type="primary", help="현재 입력한 브리프를 기준으로 전체 슬라이드 초안을 다시 생성합니다."):
            missing = [field for field in pack.required_fields if not str(st.session_state.brief.get(field, "")).strip()]
            if missing:
                st.error("필수 브리프를 먼저 입력해주세요.")
            else:
                try:
                    generated = get_default_llm().plan_slides(build_request(pack), pack.id, None)
                    st.session_state.slide_schema = apply_manual_edits(generated)
                    st.rerun()
                except Exception as exc:
                    logger.exception("Failed to generate AI draft")
                    st.error(str(exc))
    with t2:
        if st.button("선택 영역 AI 수정", key="toolbar_refine", use_container_width=True, help="현재 선택한 슬라이드 영역만 AI에게 다시 쓰도록 요청합니다."):
            instruction = st.session_state.block_instruction.strip()
            if not instruction:
                st.warning("수정 지시를 먼저 입력해주세요.")
            else:
                feedback_key = f"slide_feedback_{selected_slide.index}"
                prev = str(st.session_state.get(feedback_key, "")).strip()
                scoped = f"[{st.session_state.selected_block}] {instruction}"
                st.session_state[feedback_key] = scoped if not prev else prev + "\n" + scoped
                try:
                    generated = get_default_llm().plan_slides(build_request(pack), pack.id, None)
                    st.session_state.slide_schema = apply_manual_edits(generated)
                    st.rerun()
                except Exception as exc:
                    logger.exception("Failed to refine AI draft")
                    st.error(str(exc))
    with t3:
        if st.button("수동 편집 반영", key="toolbar_save", use_container_width=True, help="오른쪽 편집 패널에서 바꾼 내용을 현재 슬라이드 구조에 반영합니다."):
            st.session_state.slide_schema = apply_manual_edits(schema)
            st.success("현재 편집 상태를 반영했습니다.")
    with t4:
        if st.button("PPT 추출 >", key="toolbar_download", use_container_width=True, help="현재 편집 결과를 PPT 다운로드 단계로 보냅니다."):
            st.session_state.slide_schema = apply_manual_edits(schema)
            go_to_step(3)

    left, center, right = st.columns([0.62, 2.35, 0.72], gap="small")

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>입력 재료</div><div class='panel-copy'>무엇을 보고할지, 누구에게 보고할지, 어떤 메시지를 남길지 입력하는 영역입니다.</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>선택한 팩</div><div class='metric-value'>{pack.name}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>필수 입력 충족</div><div class='metric-value'>{pack_completion_ratio(pack)}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>슬라이드 수</div><div class='metric-value'>{len(schema.slides)}장</div></div>", unsafe_allow_html=True)

        with st.expander("1. 기본 정보", expanded=True):
            st.caption("이 정보는 보고서 전체의 제목 톤, 대상, 요약 방향에 영향을 줍니다.")
            for key, (label, placeholder) in COMMON_FIELDS.items():
                widget_key = f"brief_{key}"
                if widget_key not in st.session_state:
                    st.session_state[widget_key] = str(st.session_state.brief.get(key, ""))
                st.text_area(label, key=widget_key, placeholder=placeholder, height=96 if key in {"reference_material", "layout_preferences"} else 74, help="이 입력은 전체 슬라이드 구조와 문구 톤을 정하는 데 사용됩니다.")
                st.session_state.brief[key] = st.session_state.get(widget_key, "")

        with st.expander("2. 보고 재료", expanded=True):
            st.caption("선택한 보고 팩에 맞는 핵심 재료입니다. 이 내용이 각 슬라이드의 실제 본문으로 들어갑니다.")
            for key, label, placeholder in PACK_FIELDS.get(pack.id, []):
                widget_key = f"brief_{key}"
                if widget_key not in st.session_state:
                    st.session_state[widget_key] = str(st.session_state.brief.get(key, ""))
                st.text_area(label, key=widget_key, placeholder=placeholder, height=118, help="이 입력은 해당 보고 팩의 핵심 슬라이드 내용에 직접 반영됩니다.")
                st.session_state.brief[key] = st.session_state.get(widget_key, "")

        with st.expander("3. 스타일 / 색상", expanded=False):
            st.caption("미리보기와 최종 PPT에 동시에 반영되는 색상 설정입니다.")
            st.selectbox("테마 프리셋", options=list(THEME_PRESETS.keys()), key="theme_preset", on_change=sync_theme_from_preset, help="LG 기본 톤을 유지한 상태에서 색상 방향만 바꿉니다.")
            theme = current_theme()
            color_cols = st.columns(2, gap="small")
            for idx, (field, label) in enumerate(COLOR_FIELDS):
                with color_cols[idx % 2]:
                    picker_key = f"theme_{field}"
                    if picker_key not in st.session_state:
                        st.session_state[picker_key] = theme[field]
                    st.color_picker(label, key=picker_key, help="해당 색은 미리보기와 실제 PPT 출력 모두에 반영됩니다.")
                    st.session_state.theme[field] = st.session_state.get(picker_key, theme[field])
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>실시간 미리보기</div><div class='panel-copy'>실제 PPT 16:9 비율에 가깝게 보이며, 내용이 얼마나 들어가고 글씨가 어느 정도 밀도인지 더 현실적으로 확인할 수 있습니다.</div>", unsafe_allow_html=True)
        top_left, top_mid, top_right = st.columns([1.0, 2.2, 1.1], gap="small")
        with top_left:
            if st.button("< 이전", key="nav_prev", use_container_width=True, disabled=selected_idx == 1, help="이전 슬라이드로 이동합니다."):
                st.session_state.selected_slide_idx = selected_idx - 1
                st.rerun()
        with top_mid:
            options = [f"{slide.index}. {slide.content.title or slide.content.heading or slide.type.value}" for slide in schema.slides]
            labels_to_idx = {label: i + 1 for i, label in enumerate(options)}
            picked = st.selectbox("슬라이드 선택", options=options, index=selected_idx - 1, key="slide_picker", label_visibility="collapsed", help="지금 편집할 슬라이드를 고릅니다.")
            picked_idx = labels_to_idx[picked]
            if picked_idx != selected_idx:
                st.session_state.selected_slide_idx = picked_idx
                st.rerun()
        with top_right:
            st.slider("미리보기 확대", min_value=90, max_value=140, value=st.session_state.get("preview_scale", 112), step=2, key="preview_scale", help="실제 PPT와 유사한 체감 크기로 확인할 수 있도록 미리보기 크기를 조정합니다.")
        nav_note_left, nav_note_right = st.columns([1.0, 1.0])
        with nav_note_left:
            st.markdown(f"<div class='slide-meta'>슬라이드 {selected_slide.index} · {selected_slide.type.value}</div>", unsafe_allow_html=True)
        with nav_note_right:
            if st.button("다음 >", key="nav_next", use_container_width=True, disabled=selected_idx == len(schema.slides), help="다음 슬라이드로 이동합니다."):
                st.session_state.selected_slide_idx = selected_idx + 1
                st.rerun()
        scale = st.session_state.get("preview_scale", 100)
        st.markdown("<div class='preview-frame'>", unsafe_allow_html=True)
        st.markdown(f"<div style='width:min(100%, 1500px); margin:0 auto; transform:scale({scale / 100}); transform-origin: top center;'>" + preview_html(selected_slide, current_theme(), st.session_state.selected_block) + "</div><div style='height:{max(0, int((scale - 100) * 7))}px'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("변화 범위: 제목, 핵심 포인트, 표/차트 데이터, 좌우 컬럼, 색상 테마")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>슬라이드 편집</div><div class='panel-copy'>현재 슬라이드를 직접 수정하거나, 특정 영역만 AI에게 다시 쓰게 할 수 있습니다.</div>", unsafe_allow_html=True)
        move1, move2, move3 = st.columns(3, gap="small")
        with move1:
            if st.button("위로", key=f"move_up_{selected_idx}", use_container_width=True, disabled=selected_idx == 1, help="현재 슬라이드를 위로 한 칸 이동합니다."):
                schema.slides[selected_idx - 2], schema.slides[selected_idx - 1] = schema.slides[selected_idx - 1], schema.slides[selected_idx - 2]
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = selected_idx - 1
                st.rerun()
        with move2:
            if st.button("아래로", key=f"move_down_{selected_idx}", use_container_width=True, disabled=selected_idx == len(schema.slides), help="현재 슬라이드를 아래로 한 칸 이동합니다."):
                schema.slides[selected_idx - 1], schema.slides[selected_idx] = schema.slides[selected_idx], schema.slides[selected_idx - 1]
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = selected_idx + 1
                st.rerun()
        with move3:
            if st.button("삭제", key=f"delete_slide_{selected_idx}", use_container_width=True, disabled=len(schema.slides) <= 1, help="현재 슬라이드를 삭제합니다."):
                schema.slides.pop(selected_idx - 1)
                for idx, slide in enumerate(schema.slides, start=1):
                    slide.index = idx
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = max(1, min(selected_idx, len(schema.slides)))
                st.rerun()
        prefix = f"slide_{selected_slide.index}"
        with st.expander("1. 기본 설정", expanded=True):
            st.caption("이 영역은 슬라이드 종류와 제목, 주요 메시지처럼 가장 직접적인 변화를 줍니다.")
            st.selectbox("슬라이드 타입", options=[item.value for item in SlideType], key=f"{prefix}_type", help="불릿형, 표형, 좌우 비교형, 차트형 등 레이아웃 종류를 바꿉니다.")
            st.text_input("슬라이드 제목", key=f"{prefix}_title", help="상단 제목 문구가 바뀝니다.")
            st.selectbox("AI 수정 대상", options=block_options(selected_slide), key="selected_block", help="AI가 어떤 영역을 바꿀지 지정합니다.")
            st.text_area("핵심 내용 / 포인트", key=f"{prefix}_points", height=130, placeholder="슬라이드에 들어갈 핵심 문구를 줄바꿈으로 적어주세요.", help="이 내용은 본문 불릿, 요약문, 해석 포인트 등에 반영됩니다.")
            st.text_area("메모 / 추가 지시", key=f"{prefix}_notes", height=82, placeholder="강조할 수치, 위치 지시, 유첨으로 넘길 상세 설명 등을 적어주세요.", help="직접 보이는 본문보다 보조 설명이나 AI 수정 힌트에 가깝습니다.")
        current_type = SlideType(st.session_state.get(f"{prefix}_type", selected_slide.type.value))
        with st.expander("2. 레이아웃 상세", expanded=current_type in {SlideType.TWO_COLUMN, SlideType.TABLE, SlideType.CHART}):
            st.caption("표/차트/양단 비교형처럼 구조가 있는 슬라이드에서 실제 배치 내용을 바꿉니다.")
            if current_type == SlideType.TWO_COLUMN:
                st.text_input("좌측 제목", key=f"{prefix}_left_title", help="좌측 박스의 제목을 바꿉니다.")
                st.text_area("좌측 내용", key=f"{prefix}_left_points", height=92, placeholder="좌측 컬럼 내용을 줄바꿈으로 입력", help="좌측 영역 불릿이 바뀝니다.")
                st.text_input("우측 제목", key=f"{prefix}_right_title", help="우측 박스의 제목을 바꿉니다.")
                st.text_area("우측 내용", key=f"{prefix}_right_points", height=92, placeholder="우측 컬럼 내용을 줄바꿈으로 입력", help="우측 영역 불릿이 바뀝니다.")
            elif current_type == SlideType.TABLE:
                st.text_area("표 데이터", key=f"{prefix}_table", height=150, placeholder="첫 줄은 헤더, 이후 줄은 행입니다. 예: 구분 | 주요 내용 | 의미", help="표의 열 제목과 행 내용이 바뀝니다.")
            elif current_type == SlideType.CHART:
                st.text_area("차트 데이터", key=f"{prefix}_chart", height=110, placeholder="categories: 기획, 개발, 검증, 공유\nvalues: 40, 60, 75, 88", help="차트 막대 이름과 수치가 바뀝니다.")
            else:
                st.info("현재 슬라이드 타입은 별도의 구조 입력이 많지 않습니다. 기본 설정에서 제목과 핵심 포인트를 수정하면 됩니다.")
        with st.expander("3. AI 수정 지시", expanded=True):
            st.caption("선택한 영역에 대해 AI에게 어떤 방향으로 다시 써달라고 할지 구체적으로 적는 영역입니다.")
            st.text_area("이 슬라이드에 대한 구체적 오더", key="block_instruction", height=92, placeholder="예: 이 페이지는 좌우 비교로, 우측에는 지원 요청만 짧게 정리해주세요.", help="'선택 영역 AI 수정' 버튼을 누를 때 이 지시가 사용됩니다.")
        with st.expander("4. 새 슬라이드 추가", expanded=False):
            st.caption("필요한 경우 새 페이지를 추가해 구조를 확장할 수 있습니다.")
            add1, add2 = st.columns([1.0, 1.3], gap="small")
            with add1:
                new_type = st.selectbox("추가할 타입", options=[item.value for item in SlideType], key="new_slide_type", help="새로 넣을 페이지의 기본 구조를 고릅니다.")
            with add2:
                new_title = st.text_input("새 슬라이드 제목", key="new_slide_title", placeholder="예: 운영 방향 / 리스크 관리 / 상세 유첨", help="새 페이지 상단 제목입니다.")
            if st.button("슬라이드 추가", key="add_slide", use_container_width=True, help="새 슬라이드를 현재 덱 뒤에 추가합니다."):
                new_slide = Slide(index=len(schema.slides) + 1, type=SlideType(new_type), content=SlideContent(title=new_title or "새 슬라이드", heading=new_title or "새 슬라이드", points=["핵심 포인트를 여기에 입력", "필요 시 AI 수정으로 다듬기"], left_title="실행 계획", right_title="리스크 / 지원", left_points=["좌측 포인트"], right_points=["우측 포인트"], data={"headers": ["구분", "주요 내용", "의미"], "rows": [["항목", "내용", "의미"]], "categories": ["A", "B", "C", "D"], "series": [{"name": "진척", "values": [35, 50, 70, 90]}]}))
                schema.slides.append(new_slide)
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = len(schema.slides)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    foot1, foot2 = st.columns(2, gap="small")
    with foot1:
        if st.button("< 템플릿 선택으로", key="footer_back_pack", use_container_width=True, help="템플릿 선택 화면으로 돌아갑니다."):
            go_to_step(1)
    with foot2:
        if st.button("초안 리셋", key="footer_reset_schema", use_container_width=True, help="현재 초안을 처음 상태로 되돌립니다."):
            st.session_state.slide_schema = bootstrap_schema(pack)
            st.session_state.selected_slide_idx = 1
            st.rerun()


def render_download() -> None:
    pack = get_template_pack(st.session_state.selected_pack_id)
    schema = apply_manual_edits(get_schema(pack))
    theme = current_theme()
    render_header("PPT 추출", "현재 구조와 테마를 그대로 PPT 파일로 내보냅니다.")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>최종 추출</div><div class='panel-copy'>현재 보고서 구조를 확인한 뒤 바로 내려받을 수 있습니다.</div>", unsafe_allow_html=True)
    st.write(f"선택 템플릿: {pack.name}")
    st.write(f"슬라이드 수: {len(schema.slides)}장")
    st.write(f"적용 테마: {st.session_state.theme_preset}")
    ppt_bytes = render_pptx(schema, theme=theme)
    filename = re.sub(r"[^0-9A-Za-z가-힣._()\- ]+", "_", schema.meta.title or pack.name).strip() or "pptagent_deck"
    if not filename.lower().endswith(".pptx"):
        filename += ".pptx"
    st.download_button("PPT 다운로드", data=ppt_bytes, file_name=filename, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True, type="primary", key="download_ppt_file", help="현재 보고서를 .pptx 파일로 저장합니다.")
    b1, b2 = st.columns(2, gap="small")
    with b1:
        if st.button("< Studio로 돌아가기", key="download_back_studio", use_container_width=True):
            go_to_step(2)
    with b2:
        if st.button("템플릿 다시 선택", key="download_back_pack", use_container_width=True):
            go_to_step(1)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    inject_styles()
    init_state()
    if st.session_state.step == 1:
        render_pack_picker()
    elif st.session_state.step == 2:
        render_studio()
    else:
        render_download()


if __name__ == "__main__":
    main()
