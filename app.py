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

st.set_page_config(page_title="PPTAgent Studio", page_icon="??", layout="wide")

COMPANY_NAME = os.getenv("PPTAGENT_COMPANY_NAME", "LG Electronics")
CONFIDENTIAL_LABEL = os.getenv("PPTAGENT_CONFIDENTIAL_LABEL", "LGE Internal Use Only")

COMMON_FIELDS = {
    "department": ("Department / Org", "e.g. HS Division Customer Value Innovation Team"),
    "role": ("Author Role", "e.g. Manager / Part Lead / PM"),
    "audience": ("Audience", "e.g. Executive / Org Leader / Related Dept."),
    "objective": ("Report Objective", "e.g. Share this week's result and next week's support request"),
    "reference_material": ("Long Notes / Meeting Memo / Source Text", "Paste meeting notes, email drafts, or long source text here."),
    "layout_preferences": ("Preferred Layout / Emphasis", "e.g. Page 2 summary, Page 3 table, final page request items"),
}

PACK_FIELDS = {
    "weekly_exec": [
        ("period", "Report Period *", "e.g. 2026 Apr W1 (03.30 ~ 04.05)"),
        ("done", "Completed Work *", "e.g.\n- MVP architecture complete\n- Streamlit wizard UI done\n- LG renderer reflected"),
        ("plan", "Next Plan *", "e.g.\n- OpenAI quality test\n- Internal beta\n- Template sample expansion"),
        ("issues", "Issues / Requests", "e.g.\n- API budget review\n- Need more internal slide samples"),
    ],
    "project_exec": [
        ("project_name", "Project Name *", "e.g. PPTAgent"),
        ("goal", "Project Goal *", "e.g.\n- Reduce report lead time\n- Standardize internal reporting"),
        ("progress", "Progress *", "e.g.\n- UI complete\n- Renderer upgrade in progress\n- AI refinement logic designed"),
        ("risks", "Risks / Requests", "e.g.\n- Need more slide samples\n- Need budget / access review"),
    ],
    "proposal_exec": [
        ("background", "Background / Problem *", "e.g.\n- Repetitive reporting work is heavy\n- Deck quality varies by person"),
        ("solution", "Proposed Solution *", "e.g.\n- Company template platform + AI refinement agent"),
        ("effect", "Expected Impact *", "e.g.\n- Reduce creation time\n- Improve executive reporting quality"),
        ("resources", "Execution / Needed Resource", "e.g.\n- MVP upgrade\n- Gather template samples\n- Beta operation"),
    ],
}

THEME_PRESETS = {
    "LGE Core": {"primary": "#A50034", "secondary": "#2C3142", "accent": "#D9DEE8", "text": "#202532", "muted": "#6B7280", "surface": "#F7F8FB", "background": "#FFFFFF", "support": "#0E7A53", "border": "#D9DEE6"},
    "LGE Executive": {"primary": "#A50034", "secondary": "#4D5566", "accent": "#E9ECF2", "text": "#1F2937", "muted": "#7B8394", "surface": "#FBFBFC", "background": "#FFFFFF", "support": "#1B7F6B", "border": "#E3E7EE"},
    "LGE Data": {"primary": "#A50034", "secondary": "#1E3A5F", "accent": "#E8EDF6", "text": "#18212F", "muted": "#667085", "surface": "#F5F7FA", "background": "#FFFFFF", "support": "#0E7A53", "border": "#D6DCE6"},
}

COLOR_FIELDS = [("primary", "Primary"), ("secondary", "Secondary"), ("accent", "Accent"), ("background", "Background"), ("surface", "Card"), ("text", "Text"), ("muted", "Muted"), ("support", "Support"), ("border", "Border")]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f6f7fa 0%, #eef1f5 100%); }
        .block-container { max-width: 1700px; padding-top: 1rem; padding-bottom: 2.5rem; }
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
        .preview-frame { background: #eef1f5; border: 1px solid #dde2ea; border-radius: 26px; padding: 18px; }
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
    render_header("PPTAgent Studio", "LG internal reporting workspace. Stable template structure plus AI refinement for faster, better reporting.")
    st.title("Choose Report Pack")
    cols = st.columns(3, gap="large")
    for idx, pack in enumerate(list_template_packs()):
        with cols[idx % 3]:
            st.markdown("<div class='pack-card'><div class='pack-card-top'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kicker'>{pack.icon} {pack.name}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='panel-copy'>{pack.summary}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='helper'><strong>Best for</strong><br>{pack.recommended_for}</div>", unsafe_allow_html=True)
            if st.button("Start with this pack", key=f"pick_pack_{pack.id}", use_container_width=True, type="primary" if st.session_state.selected_pack_id == pack.id else "secondary"):
                st.session_state.selected_pack_id = pack.id
                st.session_state.slide_schema = bootstrap_schema(pack)
                st.session_state.selected_slide_idx = 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    _, right = st.columns([4, 1])
    with right:
        if st.button("Open Studio >", key="goto_studio", use_container_width=True, type="primary"):
            go_to_step(2)


def render_studio() -> None:
    pack = get_template_pack(st.session_state.selected_pack_id)
    schema = apply_manual_edits(get_schema(pack))
    selected_idx = min(max(1, st.session_state.selected_slide_idx), len(schema.slides))
    st.session_state.selected_slide_idx = selected_idx
    selected_slide = schema.slides[selected_idx - 1]
    ensure_slide_state(selected_slide)

    render_header("AI Studio", "Live briefing, preview, targeted AI refinement, and theme control in one screen. Visual language tuned toward LG internal reporting decks.")

    t1, t2, t3, t4 = st.columns(4, gap="small")
    with t1:
        if st.button("Generate / Refresh", key="toolbar_generate", use_container_width=True, type="primary"):
            missing = [field for field in pack.required_fields if not str(st.session_state.brief.get(field, "")).strip()]
            if missing:
                st.error("Please fill the required brief fields first.")
            else:
                try:
                    generated = get_default_llm().plan_slides(build_request(pack), pack.id, None)
                    st.session_state.slide_schema = apply_manual_edits(generated)
                    st.rerun()
                except Exception as exc:
                    logger.exception("Failed to generate AI draft")
                    st.error(str(exc))
    with t2:
        if st.button("Refine Selected Area", key="toolbar_refine", use_container_width=True):
            instruction = st.session_state.block_instruction.strip()
            if not instruction:
                st.warning("Add an instruction first.")
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
        if st.button("Apply Manual Edit", key="toolbar_save", use_container_width=True):
            st.session_state.slide_schema = apply_manual_edits(schema)
            st.success("Current edit applied.")
    with t4:
        if st.button("Export >", key="toolbar_download", use_container_width=True):
            st.session_state.slide_schema = apply_manual_edits(schema)
            go_to_step(3)

    left, center, right = st.columns([0.95, 1.35, 1.05], gap="large")

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>Brief Builder</div><div class='panel-copy'>Template stays fixed. Fill content fast and let AI reshape wording inside the template.</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>Selected Pack</div><div class='metric-value'>{pack.name}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>Required Brief</div><div class='metric-value'>{pack_completion_ratio(pack)}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'><div class='metric-label'>Slides</div><div class='metric-value'>{len(schema.slides)}</div></div>", unsafe_allow_html=True)
        for key, (label, placeholder) in COMMON_FIELDS.items():
            widget_key = f"brief_{key}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = str(st.session_state.brief.get(key, ""))
            st.text_area(label, key=widget_key, placeholder=placeholder, height=96 if key in {"reference_material", "layout_preferences"} else 74)
            st.session_state.brief[key] = st.session_state.get(widget_key, "")
        for key, label, placeholder in PACK_FIELDS.get(pack.id, []):
            widget_key = f"brief_{key}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = str(st.session_state.brief.get(key, ""))
            st.text_area(label, key=widget_key, placeholder=placeholder, height=118)
            st.session_state.brief[key] = st.session_state.get(widget_key, "")
        st.markdown("<div class='panel-title'>Theme Studio</div><div class='panel-copy'>The selected palette applies to preview and exported PPT at the same time.</div>", unsafe_allow_html=True)
        st.selectbox("Theme Preset", options=list(THEME_PRESETS.keys()), key="theme_preset", on_change=sync_theme_from_preset)
        theme = current_theme()
        color_cols = st.columns(2, gap="small")
        for idx, (field, label) in enumerate(COLOR_FIELDS):
            with color_cols[idx % 2]:
                picker_key = f"theme_{field}"
                if picker_key not in st.session_state:
                    st.session_state[picker_key] = theme[field]
                st.color_picker(label, key=picker_key)
                st.session_state.theme[field] = st.session_state.get(picker_key, theme[field])
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>Live Slide Preview</div><div class='panel-copy'>Preview updates instantly as you edit. You can validate the look before exporting PPT.</div>", unsafe_allow_html=True)
        nav1, nav2, nav3 = st.columns([1.0, 2.2, 1.0], gap="small")
        with nav1:
            if st.button("< Prev", key="nav_prev", use_container_width=True, disabled=selected_idx == 1):
                st.session_state.selected_slide_idx = selected_idx - 1
                st.rerun()
        with nav2:
            options = [f"{slide.index}. {slide.content.title or slide.content.heading or slide.type.value}" for slide in schema.slides]
            labels_to_idx = {label: i + 1 for i, label in enumerate(options)}
            picked = st.selectbox("Slide", options=options, index=selected_idx - 1, key="slide_picker", label_visibility="collapsed")
            picked_idx = labels_to_idx[picked]
            if picked_idx != selected_idx:
                st.session_state.selected_slide_idx = picked_idx
                st.rerun()
        with nav3:
            if st.button("Next >", key="nav_next", use_container_width=True, disabled=selected_idx == len(schema.slides)):
                st.session_state.selected_slide_idx = selected_idx + 1
                st.rerun()
        st.markdown(f"<div class='slide-meta'>Slide {selected_slide.index} ? {selected_slide.type.value}</div>", unsafe_allow_html=True)
        st.markdown("<div class='preview-frame'>", unsafe_allow_html=True)
        st.markdown(preview_html(selected_slide, current_theme(), st.session_state.selected_block), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption("Live fields: title, key points, table/chart data, left-right columns, theme palette")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>Inspector</div><div class='panel-copy'>Fine tune the current slide manually or ask AI to rewrite only the selected block.</div>", unsafe_allow_html=True)
        move1, move2, move3 = st.columns(3, gap="small")
        with move1:
            if st.button("Up", key=f"move_up_{selected_idx}", use_container_width=True, disabled=selected_idx == 1):
                schema.slides[selected_idx - 2], schema.slides[selected_idx - 1] = schema.slides[selected_idx - 1], schema.slides[selected_idx - 2]
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = selected_idx - 1
                st.rerun()
        with move2:
            if st.button("Down", key=f"move_down_{selected_idx}", use_container_width=True, disabled=selected_idx == len(schema.slides)):
                schema.slides[selected_idx - 1], schema.slides[selected_idx] = schema.slides[selected_idx], schema.slides[selected_idx - 1]
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = selected_idx + 1
                st.rerun()
        with move3:
            if st.button("Delete", key=f"delete_slide_{selected_idx}", use_container_width=True, disabled=len(schema.slides) <= 1):
                schema.slides.pop(selected_idx - 1)
                for idx, slide in enumerate(schema.slides, start=1):
                    slide.index = idx
                st.session_state.slide_schema = apply_manual_edits(schema)
                st.session_state.selected_slide_idx = max(1, min(selected_idx, len(schema.slides)))
                st.rerun()
        prefix = f"slide_{selected_slide.index}"
        st.selectbox("Slide Type", options=[item.value for item in SlideType], key=f"{prefix}_type")
        st.text_input("Slide Title", key=f"{prefix}_title")
        st.selectbox("AI Target", options=block_options(selected_slide), key="selected_block")
        st.text_area("Key Points", key=f"{prefix}_points", height=130, placeholder="Write one point per line.")
        st.text_area("Notes / Direction", key=f"{prefix}_notes", height=82, placeholder="Add emphasis, placement direction, appendix note, or detail.")
        current_type = SlideType(st.session_state.get(f"{prefix}_type", selected_slide.type.value))
        if current_type == SlideType.TWO_COLUMN:
            st.text_input("Left Title", key=f"{prefix}_left_title")
            st.text_area("Left Column", key=f"{prefix}_left_points", height=92, placeholder="One line per item")
            st.text_input("Right Title", key=f"{prefix}_right_title")
            st.text_area("Right Column", key=f"{prefix}_right_points", height=92, placeholder="One line per item")
        if current_type == SlideType.TABLE:
            st.text_area("Table Data", key=f"{prefix}_table", height=150, placeholder="Header row first, then one row per line. Example: Category | Main Point | Meaning")
        if current_type == SlideType.CHART:
            st.text_area("Chart Data", key=f"{prefix}_chart", height=110, placeholder="categories: Plan, Build, Test, Share\nvalues: 40, 60, 75, 88")
        st.text_area("Instruction for This Slide", key="block_instruction", height=92, placeholder="Example: Keep the right column focused only on support requests.")
        st.markdown("<div class='panel-title'>Add New Slide</div>", unsafe_allow_html=True)
        add1, add2 = st.columns([1.0, 1.3], gap="small")
        with add1:
            new_type = st.selectbox("New Type", options=[item.value for item in SlideType], key="new_slide_type")
        with add2:
            new_title = st.text_input("New Slide Title", key="new_slide_title", placeholder="Example: Operating Direction / Risk Control / Appendix")
        if st.button("Add Slide", key="add_slide", use_container_width=True):
            new_slide = Slide(index=len(schema.slides) + 1, type=SlideType(new_type), content=SlideContent(title=new_title or "New Slide", heading=new_title or "New Slide", points=["Add key point here", "Use AI refine if needed"], left_title="Plan", right_title="Risk / Support", left_points=["Left point"], right_points=["Right point"], data={"headers": ["Category", "Main Point", "Meaning"], "rows": [["Item", "Content", "Meaning"]], "categories": ["A", "B", "C", "D"], "series": [{"name": "Progress", "values": [35, 50, 70, 90]}]}))
            schema.slides.append(new_slide)
            st.session_state.slide_schema = apply_manual_edits(schema)
            st.session_state.selected_slide_idx = len(schema.slides)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    foot1, foot2 = st.columns(2, gap="small")
    with foot1:
        if st.button("< Back to Pack", key="footer_back_pack", use_container_width=True):
            go_to_step(1)
    with foot2:
        if st.button("Reset Draft", key="footer_reset_schema", use_container_width=True):
            st.session_state.slide_schema = bootstrap_schema(pack)
            st.session_state.selected_slide_idx = 1
            st.rerun()


def render_download() -> None:
    pack = get_template_pack(st.session_state.selected_pack_id)
    schema = apply_manual_edits(get_schema(pack))
    theme = current_theme()
    render_header("Export Deck", "Export the current structure and theme directly into PPT.")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Final Export</div><div class='panel-copy'>Review the current structure and download the PPT file.</div>", unsafe_allow_html=True)
    st.write(f"Selected Pack: {pack.name}")
    st.write(f"Slides: {len(schema.slides)}")
    st.write(f"Theme: {st.session_state.theme_preset}")
    ppt_bytes = render_pptx(schema, theme=theme)
    filename = re.sub(r"[^0-9A-Za-z?-?._()\- ]+", "_", schema.meta.title or pack.name).strip() or "pptagent_deck"
    if not filename.lower().endswith(".pptx"):
        filename += ".pptx"
    st.download_button("Download PPT", data=ppt_bytes, file_name=filename, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True, type="primary", key="download_ppt_file")
    b1, b2 = st.columns(2, gap="small")
    with b1:
        if st.button("< Back to Studio", key="download_back_studio", use_container_width=True):
            go_to_step(2)
    with b2:
        if st.button("Change Pack", key="download_back_pack", use_container_width=True):
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
