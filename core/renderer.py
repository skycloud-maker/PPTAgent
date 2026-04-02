"""Render a SlideSchema into a company-internal PPTX deck."""

from __future__ import annotations

import io
import logging
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from core.schema import SlideContent, SlideSchema, SlideType

logger = logging.getLogger(__name__)

COMPANY_NAME = os.getenv("PPTAGENT_COMPANY_NAME", "Internal Company")
CONFIDENTIAL_LABEL = os.getenv("PPTAGENT_CONFIDENTIAL_LABEL", "Internal Use Only")

COLOR_PRIMARY = RGBColor(0xA5, 0x00, 0x34)
COLOR_SECONDARY = RGBColor(0x3B, 0x45, 0x5A)
COLOR_ACCENT = RGBColor(0xE9, 0xD6, 0xDE)
COLOR_TEXT = RGBColor(0x2C, 0x2C, 0x2C)
COLOR_MUTED = RGBColor(0x76, 0x76, 0x76)
COLOR_BORDER = RGBColor(0xD9, 0xD9, 0xD9)
COLOR_SURFACE = RGBColor(0xF8, 0xF7, 0xF9)
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT_KO = os.getenv("PPTAGENT_FONT_KO", "Malgun Gothic")
FONT_EN = os.getenv("PPTAGENT_FONT_EN", "Arial")

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)
MARGIN_L = Inches(0.6)

ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets"))
DEFAULT_LOGO_PATH = os.path.join(ASSETS_DIR, "company_logo.png")
COMPANY_LOGO_PATH = os.getenv("PPTAGENT_LOGO_PATH", DEFAULT_LOGO_PATH)


def render_pptx(schema: SlideSchema) -> bytes:
    """Return PPTX bytes without persisting the file on disk."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]

    for slide_definition in schema.slides:
        slide = prs.slides.add_slide(blank_layout)
        logger.info(
            "Rendering slide | index=%s | type=%s",
            slide_definition.index,
            slide_definition.type.value,
        )

        if slide_definition.type == SlideType.TITLE:
            _render_title_slide(slide, slide_definition.content)
        elif slide_definition.type == SlideType.SECTION:
            _render_section_slide(slide, slide_definition.content)
        elif slide_definition.type == SlideType.BULLET:
            _render_bullet_slide(slide, slide_definition.content)
        elif slide_definition.type == SlideType.CHART:
            _render_chart_placeholder(slide, slide_definition.content)
        elif slide_definition.type == SlideType.TABLE:
            _render_table_placeholder(slide, slide_definition.content)
        elif slide_definition.type == SlideType.TWO_COLUMN:
            _render_two_column_slide(slide, slide_definition.content)
        elif slide_definition.type == SlideType.IMAGE:
            _render_image_slide(slide, slide_definition.content)
        else:
            _render_default_slide(slide, slide_definition.content)

        if slide_definition.type != SlideType.TITLE:
            _add_common_header(slide)
            _add_common_footer(slide, slide_definition.index)

    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output.getvalue()


def _add_common_header(slide) -> None:
    if os.path.exists(COMPANY_LOGO_PATH):
        slide.shapes.add_picture(
            COMPANY_LOGO_PATH,
            left=Inches(11.75),
            top=Inches(0.12),
            width=Inches(1.1),
            height=Inches(0.45),
        )
    else:
        _tb(
            slide,
            l=Inches(11.1),
            t=Inches(0.14),
            w=Inches(1.8),
            h=Inches(0.25),
            text=COMPANY_NAME,
            font=FONT_EN,
            size=9,
            bold=True,
            color=COLOR_PRIMARY,
            align=PP_ALIGN.RIGHT,
        )

    _tb(
        slide,
        l=Inches(5.55),
        t=Inches(0.12),
        w=Inches(2.2),
        h=Inches(0.25),
        text=CONFIDENTIAL_LABEL,
        font=FONT_EN,
        size=9,
        color=COLOR_MUTED,
        align=PP_ALIGN.CENTER,
    )


def _add_title_bar(slide, title_text: str) -> None:
    _tb(
        slide,
        l=MARGIN_L,
        t=Inches(0.42),
        w=Inches(11.5),
        h=Inches(0.52),
        text=title_text,
        font=FONT_KO,
        size=20,
        bold=True,
        color=COLOR_TEXT,
    )

    line = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        MARGIN_L,
        Inches(0.98),
        Inches(12.1),
        Pt(1.8),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_PRIMARY
    line.line.fill.background()


def _add_common_footer(slide, page_num: int) -> None:
    _tb(
        slide,
        l=Inches(5.8),
        t=Inches(7.0),
        w=Inches(1.7),
        h=Inches(0.25),
        text=f"{COMPANY_NAME} | {page_num}",
        font=FONT_EN,
        size=9,
        color=COLOR_MUTED,
        align=PP_ALIGN.CENTER,
    )


def _render_title_slide(slide, content: SlideContent) -> None:
    banner = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        0,
        0,
        SLIDE_W,
        Inches(1.05),
    )
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_PRIMARY
    banner.line.fill.background()

    if os.path.exists(COMPANY_LOGO_PATH):
        slide.shapes.add_picture(
            COMPANY_LOGO_PATH,
            left=Inches(11.75),
            top=Inches(0.22),
            width=Inches(1.15),
            height=Inches(0.48),
        )

    _tb(
        slide,
        l=MARGIN_L,
        t=Inches(1.8),
        w=Inches(11.7),
        h=Inches(1.3),
        text=content.title or "제목을 입력해주세요",
        font=FONT_KO,
        size=30,
        bold=True,
        color=COLOR_TEXT,
    )
    _tb(
        slide,
        l=MARGIN_L,
        t=Inches(3.15),
        w=Inches(11.0),
        h=Inches(0.6),
        text=content.subtitle or COMPANY_NAME,
        font=FONT_KO,
        size=16,
        color=COLOR_MUTED,
    )

    divider = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        MARGIN_L,
        Inches(4.1),
        Inches(12.1),
        Pt(2.2),
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_PRIMARY
    divider.line.fill.background()

    if content.presenter:
        _tb(
            slide,
            l=Inches(9.1),
            t=Inches(6.55),
            w=Inches(3.8),
            h=Inches(0.4),
            text=content.presenter,
            font=FONT_KO,
            size=11,
            color=COLOR_TEXT,
            align=PP_ALIGN.RIGHT,
        )


def _render_section_slide(slide, content: SlideContent) -> None:
    side = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        0,
        0,
        Inches(4.75),
        SLIDE_H,
    )
    side.fill.solid()
    side.fill.fore_color.rgb = COLOR_PRIMARY
    side.line.fill.background()

    _tb(
        slide,
        l=Inches(0.45),
        t=Inches(2.55),
        w=Inches(3.8),
        h=Inches(1.8),
        text=content.heading or content.title or "",
        font=FONT_KO,
        size=25,
        bold=True,
        color=COLOR_WHITE,
        align=PP_ALIGN.CENTER,
    )


def _render_bullet_slide(slide, content: SlideContent) -> None:
    _add_title_bar(slide, content.heading or content.title or "")

    for idx, point in enumerate((content.points or [])[:5]):
        _tb(
            slide,
            l=Inches(0.95),
            t=Inches(1.35 + idx * 0.95),
            w=Inches(11.1),
            h=Inches(0.65),
            text=f"• {point}",
            font=FONT_KO,
            size=15,
            color=COLOR_TEXT,
        )

    if content.notes:
        _tb(
            slide,
            l=Inches(0.95),
            t=Inches(6.2),
            w=Inches(11.0),
            h=Inches(0.45),
            text=content.notes,
            font=FONT_KO,
            size=10,
            color=COLOR_MUTED,
        )


def _render_chart_placeholder(slide, content: SlideContent) -> None:
    _add_title_bar(slide, content.heading or content.title or "")
    box = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(0.8),
        Inches(1.35),
        Inches(11.7),
        Inches(5.35),
    )
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_SURFACE
    box.line.color.rgb = COLOR_BORDER

    _tb(
        slide,
        l=Inches(1.1),
        t=Inches(3.25),
        w=Inches(11.0),
        h=Inches(0.6),
        text="[차트 영역 - 데이터 시각화용 자리]",
        font=FONT_KO,
        size=13,
        color=COLOR_MUTED,
        align=PP_ALIGN.CENTER,
    )


def _render_table_placeholder(slide, content: SlideContent) -> None:
    _add_title_bar(slide, content.heading or content.title or "")
    box = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(0.8),
        Inches(1.35),
        Inches(11.7),
        Inches(5.35),
    )
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_SURFACE
    box.line.color.rgb = COLOR_BORDER

    _tb(
        slide,
        l=Inches(1.1),
        t=Inches(3.25),
        w=Inches(11.0),
        h=Inches(0.6),
        text="[표 영역 - 표 데이터용 자리]",
        font=FONT_KO,
        size=13,
        color=COLOR_MUTED,
        align=PP_ALIGN.CENTER,
    )


def _render_two_column_slide(slide, content: SlideContent) -> None:
    _add_title_bar(slide, content.heading or content.title or "")
    divider = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(6.55),
        Inches(1.25),
        Pt(1.5),
        Inches(5.7),
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_BORDER
    divider.line.fill.background()

    _tb(
        slide,
        l=Inches(0.9),
        t=Inches(1.25),
        w=Inches(5.1),
        h=Inches(0.4),
        text=content.left_title or "항목 1",
        font=FONT_KO,
        size=14,
        bold=True,
        color=COLOR_PRIMARY,
        align=PP_ALIGN.CENTER,
    )
    _tb(
        slide,
        l=Inches(7.0),
        t=Inches(1.25),
        w=Inches(5.1),
        h=Inches(0.4),
        text=content.right_title or "항목 2",
        font=FONT_KO,
        size=14,
        bold=True,
        color=COLOR_PRIMARY,
        align=PP_ALIGN.CENTER,
    )

    for idx, point in enumerate((content.left_points or [])[:4]):
        _tb(
            slide,
            l=Inches(0.95),
            t=Inches(1.9 + idx * 0.8),
            w=Inches(5.1),
            h=Inches(0.5),
            text=f"• {point}",
            font=FONT_KO,
            size=13,
            color=COLOR_TEXT,
        )
    for idx, point in enumerate((content.right_points or [])[:4]):
        _tb(
            slide,
            l=Inches(7.05),
            t=Inches(1.9 + idx * 0.8),
            w=Inches(5.1),
            h=Inches(0.5),
            text=f"• {point}",
            font=FONT_KO,
            size=13,
            color=COLOR_TEXT,
        )


def _render_image_slide(slide, content: SlideContent) -> None:
    _add_title_bar(slide, content.heading or content.title or "")
    box = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(0.8),
        Inches(1.35),
        Inches(11.7),
        Inches(5.35),
    )
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_SURFACE
    box.line.color.rgb = COLOR_BORDER

    if content.image_path and os.path.exists(content.image_path):
        slide.shapes.add_picture(
            content.image_path,
            left=Inches(1.0),
            top=Inches(1.55),
            width=Inches(11.3),
            height=Inches(4.9),
        )
    else:
        _tb(
            slide,
            l=Inches(1.1),
            t=Inches(3.25),
            w=Inches(11.0),
            h=Inches(0.6),
            text="[이미지 영역 - 내부 시안/캡처 삽입 자리]",
            font=FONT_KO,
            size=13,
            color=COLOR_MUTED,
            align=PP_ALIGN.CENTER,
        )


def _render_default_slide(slide, content: SlideContent) -> None:
    heading = content.heading or content.title or ""
    if heading:
        _add_title_bar(slide, heading)


def _tb(
    slide,
    l: Emu,
    t: Emu,
    w: Emu,
    h: Emu,
    text: str,
    font: str = FONT_KO,
    size: int = 14,
    bold: bool = False,
    color: RGBColor = COLOR_TEXT,
    align: PP_ALIGN = PP_ALIGN.LEFT,
) -> None:
    text_box = slide.shapes.add_textbox(l, t, w, h)
    frame = text_box.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
