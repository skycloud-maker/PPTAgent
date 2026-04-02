"""Pydantic models for the intermediate slide schema."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class SlideType(str, Enum):
    """Supported slide types defined by the project architecture."""

    TITLE = "title"
    SECTION = "section"
    BULLET = "bullet"
    CHART = "chart"
    TABLE = "table"
    TWO_COLUMN = "two_column"
    IMAGE = "image"
    BLANK = "blank"


class SlideMeta(BaseModel):
    """Deck-level metadata."""

    title: str
    template: str = "company-internal"
    language: str = "ko"
    total_slides: int


class SlideContent(BaseModel):
    """Flexible content payload used by the renderer."""

    model_config = {"extra": "allow"}

    heading: str | None = None
    title: str | None = None
    subtitle: str | None = None
    presenter: str | None = None
    points: list[str] | None = None
    data: dict[str, Any] | None = None
    caption: str | None = None
    left_title: str | None = None
    right_title: str | None = None
    left_points: list[str] | None = None
    right_points: list[str] | None = None
    image_path: str | None = None
    notes: str | None = None


class Slide(BaseModel):
    """A single slide in the generated plan."""

    index: int = Field(ge=1)
    type: SlideType
    content: SlideContent

    @field_validator("content", mode="before")
    @classmethod
    def parse_content(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return SlideContent(**value)
        return value


class SlideSchema(BaseModel):
    """Intermediate representation returned by the planner."""

    meta: SlideMeta
    slides: list[Slide]

    @field_validator("slides")
    @classmethod
    def validate_slide_count(cls, slides: list[Slide]) -> list[Slide]:
        if len(slides) < 1:
            raise ValueError("슬라이드는 최소 1장 이상이어야 합니다.")
        if len(slides) > 15:
            raise ValueError("슬라이드는 최대 15장을 초과할 수 없습니다.")
        return slides

    @field_validator("slides")
    @classmethod
    def validate_first_slide_is_title(cls, slides: list[Slide]) -> list[Slide]:
        if slides and slides[0].type != SlideType.TITLE:
            raise ValueError("첫 번째 슬라이드는 반드시 title 타입이어야 합니다.")
        return slides

    @model_validator(mode="after")
    def sync_meta_total_slides(self) -> "SlideSchema":
        self.meta.total_slides = len(self.slides)
        return self
