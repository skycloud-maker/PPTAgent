"""
core/renderer.py
SlideSchema → .pptx 렌더러 (LG 브랜드 템플릿)
SECURITY.md: 파일은 메모리(BytesIO)로만 처리, 디스크 저장 없음
DESIGN.md: LG 브랜드 색상/폰트/레이아웃 규칙 적용
"""

import io
import logging
import os
import urllib.request

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from core.schema import SlideSchema, SlideType

logger = logging.getLogger(__name__)

# ── DESIGN.md 색상 팔레트 (LG 브랜드) ─────────────────────────
COLOR_PRIMARY   = RGBColor(0xA5, 0x00, 0x34)   # LG 레드
COLOR_SECONDARY = RGBColor(0x00, 0x66, 0x00)   # 풋노트 그린
COLOR_ACCENT    = RGBColor(0xFD, 0x31, 0x2E)   # 밝은 레드
COLOR_BLACK     = RGBColor(0x00, 0x00, 0x00)   # 타이틀 실선
COLOR_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_TEXT      = RGBColor(0x2C, 0x2C, 0x2C)
COLOR_GRAY_LT   = RGBColor(0xF5, 0xF5, 0xF5)
COLOR_GRAY      = RGBColor(0xD9, 0xD9, 0xD9)
COLOR_GRAY_MID  = RGBColor(0x99, 0x99, 0x99)

# ── DESIGN.md 폰트 ────────────────────────────────────────────
FONT_KO   = "LG스마트체"     # 1순위 한국어
FONT_KO_FB = "맑은 고딕"     # 2순위 fallback (python-pptx는 설치 폰트 자동 사용)
FONT_EN   = "Arial Narrow"   # 영어 고정

# ── 슬라이드 규격 16:9 ────────────────────────────────────────
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ── 공통 여백 ─────────────────────────────────────────────────
MARGIN_L = Inches(0.6)

# ── 로고 ─────────────────────────────────────────────────────
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
LOGO_PATH   = os.path.join(_ASSETS_DIR, "lg_logo.png")
LOGO_URL    = "https://pngimg.com/uploads/lg_logo/lg_logo_PNG24.png"


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def render_pptx(schema: SlideSchema) -> bytes:
    """
    SlideSchema → .pptx bytes
    SECURITY.md: 디스크 저장 없이 BytesIO로만 처리
    """
    _ensure_logo()

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    for sd in schema.slides:
        slide = prs.slides.add_slide(blank)
        logger.info(f"렌더링 | index={sd.index} | type={sd.type}")

        if sd.type == SlideType.TITLE:
            _render_title_slide(slide, sd.content)
        elif sd.type == SlideType.SECTION:
            _render_section_slide(slide, sd.content)
        elif sd.type == SlideType.BULLET:
            _render_bullet_slide(slide, sd.content)
        elif sd.type == SlideType.CHART:
            _render_chart_placeholder(slide, sd.content)
        elif sd.type == SlideType.TABLE:
            _render_table_placeholder(slide, sd.content)
        elif sd.type == SlideType.TWO_COLUMN:
            _render_two_column_slide(slide, sd.content)
        else:
            _render_default_slide(slide, sd.content)

        # 표지에는 공통 헤더/푸터 미적용
        if sd.type != SlideType.TITLE:
            _add_common_header(slide)
            _add_common_footer(slide, sd.index)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# 공통 고정 요소
# ─────────────────────────────────────────────────────────────

def _ensure_logo() -> None:
    """로고 파일 없으면 다운로드 시도"""
    if os.path.exists(LOGO_PATH):
        return
    os.makedirs(_ASSETS_DIR, exist_ok=True)
    try:
        urllib.request.urlretrieve(LOGO_URL, LOGO_PATH)
        logger.info("LG 로고 다운로드 완료")
    except Exception as e:
        logger.warning(f"LG 로고 다운로드 실패 (로고 없이 진행) | error={e}")


def _add_common_header(slide) -> None:
    """
    상단 고정 요소:
    - 우상단: LG 로고
    - 중상단: '내부 공유용' 문구
    """
    # 우상단 LG 로고
    if os.path.exists(LOGO_PATH):
        slide.shapes.add_picture(
            LOGO_PATH,
            left=Inches(12.2), top=Inches(0.08),
            width=Inches(0.85), height=Inches(0.43),
        )

    # 중상단 '내부 공유용'
    _tb(slide,
        l=Inches(5.7), t=Inches(0.07),
        w=Inches(2.0), h=Inches(0.3),
        text="내부 공유용",
        font=FONT_EN, size=9,
        color=COLOR_TEXT, align=PP_ALIGN.CENTER)


def _add_title_bar(slide, title_text: str) -> None:
    """
    좌상단 타이틀 텍스트 + 바로 아래 검은 실선
    DESIGN.md 레이아웃 규칙
    """
    _tb(slide,
        l=MARGIN_L, t=Inches(0.42),
        w=Inches(11.5), h=Inches(0.52),
        text=title_text,
        font=FONT_KO, size=20, bold=True,
        color=COLOR_BLACK)

    # 검은 실선
    line = slide.shapes.add_shape(
        1, MARGIN_L, Inches(0.98),
        Inches(12.1), Pt(1.8))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()


def _add_common_footer(slide, page_num: int) -> None:
    """중하단 페이지 번호"""
    _tb(slide,
        l=Inches(6.3), t=Inches(7.12),
        w=Inches(0.8), h=Inches(0.28),
        text=str(page_num),
        font=FONT_EN, size=9,
        color=COLOR_TEXT, align=PP_ALIGN.CENTER)


# ─────────────────────────────────────────────────────────────
# 슬라이드 타입별 렌더러
# ─────────────────────────────────────────────────────────────

def _render_title_slide(slide, content) -> None:
    """표지 슬라이드 — LG 브랜드 스타일"""
    # 상단 LG 레드 배너
    banner = slide.shapes.add_shape(
        1, 0, 0, SLIDE_W, Inches(1.1))
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_PRIMARY
    banner.line.fill.background()

    # 배너 위 LG 로고 (흰색 로고로 보이도록 우상단)
    if os.path.exists(LOGO_PATH):
        slide.shapes.add_picture(
            LOGO_PATH,
            left=Inches(12.0), top=Inches(0.3),
            width=Inches(1.0), height=Inches(0.5))

    # 메인 제목
    _tb(slide,
        l=MARGIN_L, t=Inches(1.8),
        w=Inches(11.5), h=Inches(1.5),
        text=content.title or "제목을 입력하세요",
        font=FONT_KO, size=34, bold=True,
        color=COLOR_BLACK)

    # LG 레드 구분선
    div = slide.shapes.add_shape(
        1, MARGIN_L, Inches(3.5), Inches(12.1), Pt(2.5))
    div.fill.solid()
    div.fill.fore_color.rgb = COLOR_PRIMARY
    div.line.fill.background()

    # 부제목
    if content.subtitle:
        _tb(slide,
            l=MARGIN_L, t=Inches(3.7),
            w=Inches(10.5), h=Inches(0.65),
            text=content.subtitle,
            font=FONT_KO, size=16,
            color=COLOR_TEXT)

    # 발표자 (우하단)
    if content.presenter:
        _tb(slide,
            l=Inches(9.5), t=Inches(6.75),
            w=Inches(3.5), h=Inches(0.45),
            text=content.presenter,
            font=FONT_KO, size=11,
            color=COLOR_TEXT, align=PP_ALIGN.RIGHT)


def _render_section_slide(slide, content) -> None:
    """섹션 구분 슬라이드 — 좌측 LG 레드 컬럼"""
    col = slide.shapes.add_shape(
        1, 0, 0, Inches(5.2), SLIDE_H)
    col.fill.solid()
    col.fill.fore_color.rgb = COLOR_PRIMARY
    col.line.fill.background()

    _tb(slide,
        l=Inches(0.4), t=Inches(2.8),
        w=Inches(4.4), h=Inches(1.8),
        text=content.heading or content.title or "",
        font=FONT_KO, size=26, bold=True,
        color=COLOR_WHITE, align=PP_ALIGN.CENTER)

    # 우상단 로고
    if os.path.exists(LOGO_PATH):
        slide.shapes.add_picture(
            LOGO_PATH,
            left=Inches(12.0), top=Inches(0.1),
            width=Inches(1.0), height=Inches(0.5))


def _render_bullet_slide(slide, content) -> None:
    """불릿 슬라이드"""
    heading = content.heading or content.title or ""
    points  = content.points or []

    _add_title_bar(slide, heading)

    for i, point in enumerate(points[:5]):
        _tb(slide,
            l=Inches(0.9), t=Inches(1.15 + i * 1.05),
            w=Inches(11.5), h=Inches(0.9),
            text=f"▪  {point}",
            font=FONT_KO, size=14,
            color=COLOR_TEXT)


def _render_chart_placeholder(slide, content) -> None:
    """차트 슬라이드 (Phase 3에서 실제 차트 구현)"""
    heading = content.heading or content.title or ""
    _add_title_bar(slide, heading)

    box = slide.shapes.add_shape(
        1, Inches(0.8), Inches(1.15),
        Inches(11.7), Inches(5.8))
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_GRAY_LT
    box.line.color.rgb = COLOR_GRAY

    _tb(slide,
        l=Inches(0.8), t=Inches(3.7),
        w=Inches(11.7), h=Inches(0.7),
        text="[ 차트 영역 — Phase 3에서 구현 예정 ]",
        font=FONT_EN, size=12,
        color=COLOR_GRAY_MID, align=PP_ALIGN.CENTER)


def _render_table_placeholder(slide, content) -> None:
    """표 슬라이드 (Phase 3에서 실제 표 구현)"""
    heading = content.heading or content.title or ""
    _add_title_bar(slide, heading)

    _tb(slide,
        l=Inches(0.8), t=Inches(3.7),
        w=Inches(11.7), h=Inches(0.7),
        text="[ 표 영역 — Phase 3에서 구현 예정 ]",
        font=FONT_EN, size=12,
        color=COLOR_GRAY_MID, align=PP_ALIGN.CENTER)


def _render_two_column_slide(slide, content) -> None:
    """2단 비교 슬라이드"""
    heading = content.heading or content.title or ""
    _add_title_bar(slide, heading)

    # 중앙 구분선
    div = slide.shapes.add_shape(
        1, Inches(6.55), Inches(1.2),
        Pt(1.5), Inches(6.0))
    div.fill.solid()
    div.fill.fore_color.rgb = COLOR_GRAY
    div.line.fill.background()

    extra = content.model_extra or {}
    _tb(slide,
        l=Inches(0.8), t=Inches(1.2),
        w=Inches(5.5), h=Inches(0.5),
        text=extra.get("left_title", "항목 1"),
        font=FONT_KO, size=14, bold=True,
        color=COLOR_PRIMARY, align=PP_ALIGN.CENTER)

    _tb(slide,
        l=Inches(7.0), t=Inches(1.2),
        w=Inches(5.5), h=Inches(0.5),
        text=extra.get("right_title", "항목 2"),
        font=FONT_KO, size=14, bold=True,
        color=COLOR_PRIMARY, align=PP_ALIGN.CENTER)


def _render_default_slide(slide, content) -> None:
    """기본 슬라이드"""
    heading = content.heading or content.title or ""
    if heading:
        _add_title_bar(slide, heading)


# ─────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────

def _tb(
    slide,
    l: Emu, t: Emu, w: Emu, h: Emu,
    text: str,
    font: str = FONT_KO,
    size: int = 14,
    bold: bool = False,
    color: RGBColor = None,
    align: PP_ALIGN = PP_ALIGN.LEFT,
) -> None:
    """텍스트 박스 생성 헬퍼 (내부용)"""
    txBox = slide.shapes.add_textbox(l, t, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name  = font
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color or COLOR_TEXT
