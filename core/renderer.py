"""
core/renderer.py
SlideSchema → .pptx 파일 렌더러
SECURITY.md: 파일은 메모리(BytesIO)로만 처리, 디스크 저장 없음
"""

import io
import logging

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from core.schema import SlideSchema, SlideType

logger = logging.getLogger(__name__)

# DESIGN.md 색상 팔레트
COLOR_PRIMARY = RGBColor(0x1E, 0x3A, 0x5F)
COLOR_SECONDARY = RGBColor(0x2E, 0x75, 0xB6)
COLOR_ACCENT = RGBColor(0xBD, 0xD7, 0xEE)
COLOR_BG = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_TEXT = RGBColor(0x2C, 0x2C, 0x2C)
COLOR_TEXT_SUB = RGBColor(0x76, 0x76, 0x76)

# DESIGN.md 슬라이드 규격 (16:9)
SLIDE_WIDTH = Inches(13.33)
SLIDE_HEIGHT = Inches(7.5)


def render_pptx(schema: SlideSchema) -> bytes:
    """
    SlideSchema를 받아 .pptx 파일을 bytes로 반환한다.
    SECURITY.md: 디스크에 저장하지 않고 메모리(BytesIO)로만 처리

    Args:
        schema: 검증된 SlideSchema

    Returns:
        bytes: .pptx 파일 바이트
    """
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # 빈 레이아웃 사용 (인덱스 6: 완전히 빈 슬라이드)
    blank_layout = prs.slide_layouts[6]

    for slide_data in schema.slides:
        slide = prs.slides.add_slide(blank_layout)
        logger.info(f"슬라이드 렌더링 | index={slide_data.index} | type={slide_data.type}")

        if slide_data.type == SlideType.TITLE:
            _render_title_slide(slide, slide_data.content)
        elif slide_data.type == SlideType.SECTION:
            _render_section_slide(slide, slide_data.content)
        elif slide_data.type == SlideType.BULLET:
            _render_bullet_slide(slide, slide_data.content)
        elif slide_data.type == SlideType.CHART:
            _render_chart_placeholder(slide, slide_data.content)
        elif slide_data.type == SlideType.TABLE:
            _render_table_placeholder(slide, slide_data.content)
        else:
            _render_default_slide(slide, slide_data.content)

        # 슬라이드 번호 추가 (DESIGN.md)
        _add_slide_number(slide, slide_data.index)

    # 메모리에서 bytes로 변환 (디스크 저장 없음 — SECURITY.md)
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _add_text_box(slide, left, top, width, height, text, font_size, bold=False, color=None, align=PP_ALIGN.LEFT):
    """텍스트 박스 헬퍼 함수"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color or COLOR_TEXT
    return txBox


def _add_background(slide, color: RGBColor):
    """슬라이드 배경색 설정"""
    from pptx.util import Inches
    bg = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        0, 0, SLIDE_WIDTH, SLIDE_HEIGHT
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()


def _render_title_slide(slide, content) -> None:
    """표지 슬라이드 렌더링 (DESIGN.md title 레이아웃)"""
    _add_background(slide, COLOR_PRIMARY)

    title = content.title or "제목"
    subtitle = content.subtitle or ""
    presenter = content.presenter or ""

    # 제목
    _add_text_box(
        slide,
        Inches(1.5), Inches(2.5), Inches(10), Inches(1.5),
        title, 36, bold=True,
        color=RGBColor(0xFF, 0xFF, 0xFF),
        align=PP_ALIGN.CENTER,
    )

    # 부제목
    if subtitle:
        _add_text_box(
            slide,
            Inches(1.5), Inches(4.2), Inches(10), Inches(0.8),
            subtitle, 18,
            color=RGBColor(0xBD, 0xD7, 0xEE),
            align=PP_ALIGN.CENTER,
        )

    # 발표자
    if presenter:
        _add_text_box(
            slide,
            Inches(9), Inches(6.5), Inches(3.5), Inches(0.5),
            presenter, 12,
            color=RGBColor(0xFF, 0xFF, 0xFF),
            align=PP_ALIGN.RIGHT,
        )


def _render_section_slide(slide, content) -> None:
    """섹션 구분 슬라이드 렌더링"""
    # 좌측 컬럼 배경
    left_bg = slide.shapes.add_shape(
        1, 0, 0, Inches(4.5), SLIDE_HEIGHT
    )
    left_bg.fill.solid()
    left_bg.fill.fore_color.rgb = COLOR_SECONDARY
    left_bg.line.fill.background()

    heading = content.heading or content.title or ""
    _add_text_box(
        slide,
        Inches(0.5), Inches(3), Inches(3.5), Inches(1.5),
        heading, 28, bold=True,
        color=RGBColor(0xFF, 0xFF, 0xFF),
        align=PP_ALIGN.CENTER,
    )


def _render_bullet_slide(slide, content) -> None:
    """불릿 슬라이드 렌더링 (DESIGN.md bullet 레이아웃)"""
    heading = content.heading or content.title or ""
    points = content.points or []

    # 제목 영역 (상단 20%)
    _add_text_box(
        slide,
        Inches(0.5), Inches(0.3), Inches(12), Inches(1),
        heading, 28, bold=True, color=COLOR_PRIMARY,
    )

    # 구분선
    line = slide.shapes.add_shape(1, Inches(0.5), Inches(1.4), Inches(12), Pt(2))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_SECONDARY
    line.line.fill.background()

    # 불릿 포인트 (최대 5개 — QUALITY_SCORE.md)
    for i, point in enumerate(points[:5]):
        _add_text_box(
            slide,
            Inches(0.8), Inches(1.7 + i * 0.95), Inches(11.5), Inches(0.8),
            f"• {point}", 16, color=COLOR_TEXT,
        )


def _render_chart_placeholder(slide, content) -> None:
    """차트 슬라이드 — Phase 3에서 실제 차트로 구현 예정"""
    heading = content.heading or content.title or ""
    _add_text_box(
        slide,
        Inches(0.5), Inches(0.3), Inches(12), Inches(1),
        heading, 28, bold=True, color=COLOR_PRIMARY,
    )
    # 차트 영역 플레이스홀더
    placeholder = slide.shapes.add_shape(
        1, Inches(1), Inches(1.5), Inches(11), Inches(5)
    )
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = COLOR_ACCENT
    placeholder.line.color.rgb = COLOR_SECONDARY

    _add_text_box(
        slide,
        Inches(1), Inches(3.5), Inches(11), Inches(1),
        "[ 차트 영역 — Phase 3에서 구현 예정 ]", 14,
        color=COLOR_TEXT_SUB, align=PP_ALIGN.CENTER,
    )


def _render_table_placeholder(slide, content) -> None:
    """표 슬라이드 — Phase 3에서 실제 표로 구현 예정"""
    heading = content.heading or content.title or ""
    _add_text_box(
        slide,
        Inches(0.5), Inches(0.3), Inches(12), Inches(1),
        heading, 28, bold=True, color=COLOR_PRIMARY,
    )
    _add_text_box(
        slide,
        Inches(1), Inches(3.5), Inches(11), Inches(1),
        "[ 표 영역 — Phase 3에서 구현 예정 ]", 14,
        color=COLOR_TEXT_SUB, align=PP_ALIGN.CENTER,
    )


def _render_default_slide(slide, content) -> None:
    """기본 슬라이드 렌더링"""
    heading = content.heading or content.title or ""
    if heading:
        _add_text_box(
            slide,
            Inches(0.5), Inches(0.3), Inches(12), Inches(1),
            heading, 28, bold=True, color=COLOR_PRIMARY,
        )


def _add_slide_number(slide, index: int) -> None:
    """슬라이드 번호 추가 (우하단 — DESIGN.md)"""
    _add_text_box(
        slide,
        Inches(11.8), Inches(7.0), Inches(1), Inches(0.4),
        str(index), 10,
        color=COLOR_TEXT_SUB, align=PP_ALIGN.RIGHT,
    )
