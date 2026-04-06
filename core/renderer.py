"""Render a SlideSchema into a company-internal PPTX deck."""

from __future__ import annotations

import io
import os

from dotenv import load_dotenv
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from core.schema import SlideContent, SlideSchema, SlideType

load_dotenv()

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)
FONT_KO = os.getenv("PPTAGENT_FONT_KO", "Malgun Gothic")
FONT_EN = os.getenv("PPTAGENT_FONT_EN", "Arial Narrow")
COMPANY_NAME = os.getenv("PPTAGENT_COMPANY_NAME", "Your Company")
CONFIDENTIAL_LABEL = os.getenv("PPTAGENT_CONFIDENTIAL_LABEL", "Internal Use Only")
ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets"))
DEFAULT_LOGO_PATH = os.path.join(ASSETS_DIR, "company_logo.png")
COMPANY_LOGO_PATH = os.getenv("PPTAGENT_LOGO_PATH", DEFAULT_LOGO_PATH)


def _rgb(hex_code: str) -> RGBColor:
    value = hex_code.strip().lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _palette(theme: dict | None = None) -> dict[str, RGBColor]:
    theme = theme or {}
    return {
        "primary": _rgb(theme.get("primary", "#A50034")),
        "secondary": _rgb(theme.get("secondary", "#2E4A7D")),
        "accent": _rgb(theme.get("accent", "#E7D5DD")),
        "text": _rgb(theme.get("text", "#1F2937")),
        "muted": _rgb(theme.get("muted", "#6B7280")),
        "surface": _rgb(theme.get("surface", "#F7F8FA")),
        "background": _rgb(theme.get("background", "#FFFFFF")),
        "green": _rgb(theme.get("support", "#0F7B6C")),
        "border": _rgb(theme.get("border", "#D8DCE3")),
    }


def render_pptx(schema: SlideSchema, theme: dict | None = None) -> bytes:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]
    palette = _palette(theme)

    for slide_def in schema.slides:
        slide = prs.slides.add_slide(blank_layout)
        if slide_def.type == SlideType.TITLE:
            _render_title_slide(slide, slide_def.content, palette)
        elif slide_def.type == SlideType.BULLET:
            _render_bullet_slide(slide, slide_def.content, palette)
        elif slide_def.type == SlideType.TABLE:
            _render_table_slide(slide, slide_def.content, palette)
        elif slide_def.type == SlideType.TWO_COLUMN:
            _render_two_column_slide(slide, slide_def.content, palette)
        elif slide_def.type == SlideType.CHART:
            _render_chart_slide(slide, slide_def.content, palette)
        elif slide_def.type == SlideType.IMAGE:
            _render_image_slide(slide, slide_def.content, palette)
        else:
            _render_bullet_slide(slide, slide_def.content, palette)

        if slide_def.type != SlideType.TITLE:
            _add_header(slide, palette)
            _add_footer(slide, slide_def.index, palette)

    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()


def _add_header(slide, palette: dict[str, RGBColor]) -> None:
    _tb(slide, Inches(5.35), Inches(0.08), Inches(2.6), Inches(0.22), CONFIDENTIAL_LABEL, font=FONT_EN, size=9, color=palette["muted"], align=PP_ALIGN.CENTER)
    if os.path.exists(COMPANY_LOGO_PATH):
        slide.shapes.add_picture(COMPANY_LOGO_PATH, Inches(11.55), Inches(0.08), Inches(1.2), Inches(0.42))
    else:
        _tb(slide, Inches(10.9), Inches(0.08), Inches(1.8), Inches(0.22), COMPANY_NAME, font=FONT_EN, size=10, bold=True, color=palette["text"], align=PP_ALIGN.RIGHT)


def _add_footer(slide, page_num: int, palette: dict[str, RGBColor]) -> None:
    _tb(slide, Inches(5.4), Inches(7.0), Inches(2.5), Inches(0.2), f"{COMPANY_NAME} | {page_num}", font=FONT_EN, size=9, color=palette["muted"], align=PP_ALIGN.CENTER)


def _title_rule(slide, title: str, palette: dict[str, RGBColor]) -> None:
    _tb(slide, Inches(0.58), Inches(0.42), Inches(11.7), Inches(0.42), title, size=22, bold=True, color=palette["text"])
    line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.58), Inches(0.96), Inches(12.0), Pt(1.4))
    line.fill.solid()
    line.fill.fore_color.rgb = palette["text"]
    line.line.fill.background()


def _render_title_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    top_bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, SLIDE_W, Pt(6))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = palette["primary"]
    top_bar.line.fill.background()

    left_band = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, Inches(0.62), Pt(14), Inches(1.65))
    left_band.fill.solid()
    left_band.fill.fore_color.rgb = palette["primary"]
    left_band.line.fill.background()

    left_foot = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, Inches(2.15), Inches(0.72), Pt(14))
    left_foot.fill.solid()
    left_foot.fill.fore_color.rgb = palette["primary"]
    left_foot.line.fill.background()

    right_band = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(12.42), Inches(6.62), Inches(0.91), Pt(12))
    right_band.fill.solid()
    right_band.fill.fore_color.rgb = palette["primary"]
    right_band.line.fill.background()

    _tb(slide, Inches(5.2), Inches(0.08), Inches(2.8), Inches(0.22), CONFIDENTIAL_LABEL, font=FONT_EN, size=9, color=palette["primary"], align=PP_ALIGN.CENTER)
    _tb(slide, Inches(0.95), Inches(0.35), Inches(7.4), Inches(0.75), content.caption or "고정 템플릿 기반으로 빠르게 보고 초안을 만들고, AI가 문구를 임원 보고 수준으로 다듬습니다.", size=11, color=palette["text"])
    _tb(slide, Inches(1.42), Inches(2.18), Inches(10.0), Inches(1.0), content.title or "발표 제목", size=27, bold=True, color=palette["secondary"])
    _tb(slide, Inches(1.95), Inches(3.55), Inches(8.8), Inches(0.5), content.subtitle or COMPANY_NAME, size=17, color=palette["text"])
    for idx, point in enumerate((content.points or [])[:4], start=1):
        _tb(slide, Inches(1.62), Inches(4.28 + (idx - 1) * 0.46), Inches(9.0), Inches(0.3), f"{idx}. {point}", size=14, color=palette["text"])
    _tb(slide, Inches(1.48), Inches(6.53), Inches(4.5), Inches(0.3), content.presenter or COMPANY_NAME, size=12, bold=True, color=palette["secondary"])
    _tb(slide, Inches(6.0), Inches(6.53), Inches(1.7), Inches(0.3), "| CONFIDENTIAL |", font=FONT_EN, size=10, bold=True, color=palette["primary"], align=PP_ALIGN.CENTER)
    if os.path.exists(COMPANY_LOGO_PATH):
        slide.shapes.add_picture(COMPANY_LOGO_PATH, Inches(11.1), Inches(6.15), Inches(1.38), Inches(0.55))
    else:
        _tb(slide, Inches(10.8), Inches(6.18), Inches(1.8), Inches(0.35), COMPANY_NAME, font=FONT_EN, size=18, bold=True, color=palette["primary"], align=PP_ALIGN.RIGHT)
def _render_bullet_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    _title_rule(slide, content.heading or content.title or "핵심 정리", palette)
    panel = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.78), Inches(1.28), Inches(11.8), Inches(5.55))
    panel.fill.solid()
    panel.fill.fore_color.rgb = palette["background"]
    panel.line.color.rgb = palette["border"]
    for idx, point in enumerate((content.points or [])[:6]):
        top = Inches(1.58 + idx * 0.72)
        bullet = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, Inches(0.98), top + Pt(5), Pt(9), Pt(9))
        bullet.fill.solid()
        bullet.fill.fore_color.rgb = palette["primary"] if idx < 2 else palette["secondary"]
        bullet.line.fill.background()
        _tb(slide, Inches(1.18), top, Inches(10.8), Inches(0.36), point, size=15 if idx < 2 else 14, bold=idx < 2, color=palette["text"])


def _render_table_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    _title_rule(slide, content.heading or content.title or "구조화 표", palette)
    data = content.data or {}
    headers = data.get("headers") or ["항목", "내용", "의미"]
    rows = data.get("rows") or [["예시", "실제 내용을 넣어주세요", "의미"]]
    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(0.86), Inches(1.52), Inches(11.2), Inches(4.95))
    table = table_shape.table
    widths = [Inches(1.9), Inches(6.2), Inches(3.1)]
    for idx in range(min(len(headers), len(widths))):
        table.columns[idx].width = widths[idx]
    for col_idx, header in enumerate(headers):
        _set_cell(table.cell(0, col_idx), header, fill=palette["primary"], color=palette["background"], size=12, bold=True, align=PP_ALIGN.CENTER)
    for row_idx, row in enumerate(rows, start=1):
        for col_idx in range(len(headers)):
            value = row[col_idx] if col_idx < len(row) else ""
            fill = palette["surface"] if row_idx % 2 == 0 else palette["background"]
            align = PP_ALIGN.CENTER if col_idx == 0 else PP_ALIGN.LEFT
            _set_cell(table.cell(row_idx, col_idx), str(value), fill=fill, color=palette["text"], size=11, align=align)


def _render_two_column_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    _title_rule(slide, content.heading or content.title or "비교 정리", palette)
    left = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.84), Inches(1.44), Inches(5.52), Inches(5.0))
    right = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(6.86), Inches(1.44), Inches(5.52), Inches(5.0))
    for panel, fill in [(left, palette["background"]), (right, palette["surface"] )]:
        panel.fill.solid()
        panel.fill.fore_color.rgb = fill
        panel.line.color.rgb = palette["border"]
    _tb(slide, Inches(1.08), Inches(1.72), Inches(5.0), Inches(0.28), content.left_title or "현재", size=15, bold=True, color=palette["primary"], align=PP_ALIGN.CENTER)
    _tb(slide, Inches(7.1), Inches(1.72), Inches(5.0), Inches(0.28), content.right_title or "향후", size=15, bold=True, color=palette["primary"], align=PP_ALIGN.CENTER)
    for idx, point in enumerate((content.left_points or [])[:5]):
        _tb(slide, Inches(1.08), Inches(2.18 + idx * 0.62), Inches(4.85), Inches(0.35), f"• {point}", size=13, color=palette["text"])
    for idx, point in enumerate((content.right_points or [])[:5]):
        _tb(slide, Inches(7.08), Inches(2.18 + idx * 0.62), Inches(4.85), Inches(0.35), f"• {point}", size=13, color=palette["text"])
    arrow = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.CHEVRON, Inches(6.26), Inches(3.2), Inches(0.32), Inches(0.7))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = palette["accent"]
    arrow.line.fill.background()


def _render_chart_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    _title_rule(slide, content.heading or content.title or "지표 추이", palette)
    panel = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.78), Inches(1.28), Inches(11.8), Inches(5.55))
    panel.fill.solid()
    panel.fill.fore_color.rgb = palette["background"]
    panel.line.color.rgb = palette["border"]
    raw = content.data or {}
    categories = raw.get("categories") or ["1", "2", "3", "4"]
    series = raw.get("series") or [{"name": "완료율", "values": [60, 75, 82, 90]}]
    chart_data = CategoryChartData()
    chart_data.categories = categories
    for idx, item in enumerate(series):
        chart_data.add_series(item.get("name") or f"Series {idx+1}", item.get("values") or [0 for _ in categories])
    chart_shape = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1.0), Inches(1.72), Inches(6.8), Inches(4.3), chart_data)
    chart = chart_shape.chart
    chart.has_legend = len(series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.font.size = Pt(10)
    chart.value_axis.has_major_gridlines = True
    palette_list = [palette["primary"], palette["secondary"], palette["green"], palette["accent"]]
    for idx, serie in enumerate(chart.series):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = palette_list[idx % len(palette_list)]
    box = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(8.15), Inches(1.72), Inches(3.6), Inches(4.3))
    box.fill.solid()
    box.fill.fore_color.rgb = palette["surface"]
    box.line.color.rgb = palette["border"]
    _tb(slide, Inches(8.42), Inches(1.96), Inches(2.9), Inches(0.25), "해석 포인트", size=14, bold=True, color=palette["primary"])
    for idx, point in enumerate((content.points or [])[:5]):
        _tb(slide, Inches(8.42), Inches(2.34 + idx * 0.55), Inches(2.95), Inches(0.34), f"• {point}", size=12, color=palette["text"])


def _render_image_slide(slide, content: SlideContent, palette: dict[str, RGBColor]) -> None:
    _title_rule(slide, content.heading or content.title or "사례", palette)
    left = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.82), Inches(1.42), Inches(6.0), Inches(5.05))
    left.fill.solid()
    left.fill.fore_color.rgb = palette["background"]
    left.line.color.rgb = palette["border"]
    if content.image_path and os.path.exists(content.image_path):
        slide.shapes.add_picture(content.image_path, Inches(1.04), Inches(1.65), Inches(5.55), Inches(4.58))
    else:
        _tb(slide, Inches(1.05), Inches(3.6), Inches(5.5), Inches(0.4), "이미지/캡처 영역", size=13, color=palette["muted"], align=PP_ALIGN.CENTER)
    right = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(7.02), Inches(1.42), Inches(5.3), Inches(5.05))
    right.fill.solid()
    right.fill.fore_color.rgb = palette["background"]
    right.line.color.rgb = palette["border"]
    _tb(slide, Inches(7.24), Inches(1.72), Inches(4.8), Inches(0.25), content.caption or "관찰/인사이트", font=FONT_EN, size=13, bold=True, color=palette["primary"])
    for idx, point in enumerate((content.points or [])[:6]):
        _tb(slide, Inches(7.22), Inches(2.15 + idx * 0.53), Inches(4.75), Inches(0.35), point, size=12, color=palette["text"])


def _tb(slide, l: Emu, t: Emu, w: Emu, h: Emu, text: str, font: str = FONT_KO, size: int = 14, bold: bool = False, color: RGBColor | None = None, align: PP_ALIGN = PP_ALIGN.LEFT) -> None:
    box = slide.shapes.add_textbox(l, t, w, h)
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    para = frame.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def _set_cell(cell, text: str, fill: RGBColor, color: RGBColor, size: int, bold: bool = False, align: PP_ALIGN = PP_ALIGN.LEFT) -> None:
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.text_frame.clear()
    para = cell.text_frame.paragraphs[0]
    para.alignment = align
    cell.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    run = para.add_run()
    run.text = text
    run.font.name = FONT_KO
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color