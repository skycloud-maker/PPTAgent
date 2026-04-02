"""
core/schema.py
슬라이드 데이터 구조 정의 (Pydantic 모델)
ARCHITECTURE.md의 Slide Schema 구조를 코드로 구현
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, field_validator


class SlideType(str, Enum):
    """ARCHITECTURE.md에 정의된 슬라이드 타입"""
    TITLE = "title"
    SECTION = "section"
    BULLET = "bullet"
    CHART = "chart"
    TABLE = "table"
    TWO_COLUMN = "two_column"
    IMAGE = "image"
    BLANK = "blank"


class SlideMeta(BaseModel):
    """장표 전체 메타 정보"""
    title: str
    template: str = "corporate-blue"
    language: str = "ko"
    total_slides: int


class SlideContent(BaseModel):
    """슬라이드 콘텐츠 (타입별로 자유로운 구조)"""
    model_config = {"extra": "allow"}

    heading: str | None = None
    title: str | None = None
    subtitle: str | None = None
    points: list[str] | None = None
    data: dict[str, Any] | None = None


class Slide(BaseModel):
    """개별 슬라이드"""
    index: int
    type: SlideType
    content: SlideContent

    @field_validator("content", mode="before")
    @classmethod
    def parse_content(cls, v: Any) -> Any:
        """딕셔너리를 SlideContent로 변환"""
        if isinstance(v, dict):
            return SlideContent(**v)
        return v


class SlideSchema(BaseModel):
    """
    AI Planner가 출력하는 전체 슬라이드 스키마
    이 스키마가 AI Planner와 Renderer 사이의 핵심 계약(Contract)
    """
    meta: SlideMeta
    slides: list[Slide]

    @field_validator("slides")
    @classmethod
    def validate_slide_count(cls, v: list[Slide]) -> list[Slide]:
        """QUALITY_SCORE.md 기준: 최소 5장, 최대 15장"""
        if len(v) < 1:
            raise ValueError("슬라이드는 최소 1장 이상이어야 합니다")
        if len(v) > 15:
            raise ValueError("슬라이드는 최대 15장을 초과할 수 없습니다")
        return v

    @field_validator("slides")
    @classmethod
    def validate_first_slide_is_title(cls, v: list[Slide]) -> list[Slide]:
        """QUALITY_SCORE.md 기준: 첫 번째 슬라이드는 표지"""
        if v and v[0].type != SlideType.TITLE:
            raise ValueError("첫 번째 슬라이드는 title 타입이어야 합니다")
        return v
