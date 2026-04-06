"""Mock LLM adapter — API 키 없이 테스트용 슬라이드 스키마를 반환한다.

사용자가 입력한 실제 내용을 슬라이드에 반영한다.
"""

from __future__ import annotations

import logging

from core.llm.interface import LLMInterface
from core.schema import Slide, SlideContent, SlideMeta, SlideSchema, SlideType

logger = logging.getLogger(__name__)


class MockAdapter(LLMInterface):
    """API 키 없이 테스트용으로 사용하는 Mock LLM 어댑터."""

    def plan_slides(self, user_request: str, template: str, data: dict | None = None) -> SlideSchema:
        logger.info("Mock 모드 슬라이드 생성 | template=%s", template)
        fields = self._parse_fields(user_request)

        if template == "weekly_report":
            return self._build_weekly_report(fields)
        elif template == "project_status":
            return self._build_project_status(fields)
        elif template == "proposal":
            return self._build_proposal(fields)
        elif template == "data_report":
            return self._build_data_report(fields)
        else:
            return self._build_generic(fields)

    def _parse_fields(self, user_request: str) -> dict[str, str]:
        """user_request에서 [필드명] 섹션을 파싱한다."""
        fields: dict[str, str] = {}
        current_key = None
        current_lines: list[str] = []
        for line in user_request.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                if current_key:
                    fields[current_key] = "\n".join(current_lines).strip()
                current_key = stripped[1:-1]
                current_lines = []
            elif current_key:
                current_lines.append(line)
        if current_key:
            fields[current_key] = "\n".join(current_lines).strip()
        return fields

    def _to_bullets(self, text: str, max_items: int = 5) -> list[str]:
        """텍스트를 불릿 리스트로 변환"""
        lines = []
        for line in text.splitlines():
            line = line.strip().lstrip("-·•▪·").strip()
            if line:
                lines.append(line)
        return lines[:max_items]

    def _build_weekly_report(self, f: dict) -> SlideSchema:
        period = f.get("보고 기간", "")
        done   = f.get("완료 업무", "")
        plan   = f.get("다음 계획", "")
        issues = f.get("이슈 및 특이사항", "")

        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(
                title="주간 업무 보고",
                subtitle=period or "보고 기간",
                presenter="담당팀",
            )),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(
                heading="이번 주 주요 업무",
                points=self._to_bullets(done) or ["주요 업무 항목을 입력해주세요"],
            )),
            Slide(index=3, type=SlideType.BULLET, content=SlideContent(
                heading="다음 주 계획",
                points=self._to_bullets(plan) or ["계획 항목을 입력해주세요"],
            )),
        ]
        if issues.strip():
            slides.append(Slide(index=4, type=SlideType.BULLET, content=SlideContent(
                heading="이슈 / 특이사항",
                points=self._to_bullets(issues),
                caption="※ 이슈별 세부 대응 방안은 유첨 참고",
            )))

        return SlideSchema(
            meta=SlideMeta(
                title=f"주간 업무 보고 ({period})" if period else "주간 업무 보고",
                template="weekly_report", language="ko", total_slides=len(slides)),
            slides=slides)

    def _build_project_status(self, f: dict) -> SlideSchema:
        name     = f.get("프로젝트명", "프로젝트")
        period   = f.get("보고 기간", "")
        goal     = f.get("프로젝트 목표", "")
        progress = f.get("진행 현황", "")
        risks    = f.get("리스크 및 대응", "")

        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(
                title=name,
                subtitle=f"프로젝트 현황 보고 | {period}" if period else "프로젝트 현황 보고",
                presenter="담당팀",
            )),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(
                heading="프로젝트 개요 및 목표",
                points=self._to_bullets(goal) or ["목표를 입력해주세요"],
            )),
            Slide(index=3, type=SlideType.BULLET, content=SlideContent(
                heading="현재 진행 현황",
                points=self._to_bullets(progress) or ["진행 현황을 입력해주세요"],
            )),
        ]
        if risks.strip():
            slides.append(Slide(index=4, type=SlideType.BULLET, content=SlideContent(
                heading="리스크 및 대응 방안",
                points=self._to_bullets(risks),
                caption="※ 세부 대응 계획은 유첨 참고",
            )))

        return SlideSchema(
            meta=SlideMeta(title=f"{name} 현황 보고",
                           template="project_status", language="ko", total_slides=len(slides)),
            slides=slides)

    def _build_proposal(self, f: dict) -> SlideSchema:
        background = f.get("제안 배경 / 문제 정의", "") or f.get("배경 및 문제 정의", "")
        solution   = f.get("핵심 제안 내용", "")
        effect     = f.get("기대 효과", "")
        resources  = f.get("필요 자원 및 실행 계획", "")

        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(
                title="신규 기획안 제안",
                subtitle=self._to_bullets(background, 1)[0] if background else "제안 개요",
                presenter="제안팀",
            )),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(
                heading="제안 배경 / 문제 정의",
                points=self._to_bullets(background) or ["배경을 입력해주세요"],
            )),
            Slide(index=3, type=SlideType.BULLET, content=SlideContent(
                heading="핵심 제안 내용",
                points=self._to_bullets(solution) or ["제안 내용을 입력해주세요"],
            )),
            Slide(index=4, type=SlideType.BULLET, content=SlideContent(
                heading="기대 효과",
                points=self._to_bullets(effect) or ["기대 효과를 입력해주세요"],
            )),
        ]
        if resources.strip():
            slides.append(Slide(index=5, type=SlideType.BULLET, content=SlideContent(
                heading="실행 계획",
                points=self._to_bullets(resources),
            )))

        return SlideSchema(
            meta=SlideMeta(title="신규 기획안 제안",
                           template="proposal", language="ko", total_slides=len(slides)),
            slides=slides)

    def _build_data_report(self, f: dict) -> SlideSchema:
        title      = f.get("분석 제목", "데이터 분석 리포트")
        background = f.get("분석 배경 및 목적", "") or f.get("배경 및 문제 정의", "")
        direction  = f.get("분석 방향", "")

        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(
                title=title,
                subtitle="분석 결과 보고",
                presenter="분석팀",
            )),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(
                heading="분석 배경 및 목적",
                points=self._to_bullets(background) or ["분석 배경을 입력해주세요"],
            )),
            Slide(index=3, type=SlideType.CHART, content=SlideContent(
                heading="주요 지표 현황",
                caption="※ 데이터 기준 및 출처는 유첨 참고",
            )),
        ]
        if direction.strip():
            slides.append(Slide(index=4, type=SlideType.BULLET, content=SlideContent(
                heading="개선 방향",
                points=self._to_bullets(direction),
            )))

        return SlideSchema(
            meta=SlideMeta(title=title,
                           template="data_report", language="ko", total_slides=len(slides)),
            slides=slides)

    def _build_generic(self, f: dict) -> SlideSchema:
        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(
                title="발표 자료", subtitle="내부 공유용", presenter="작성팀")),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(
                heading="주요 내용", points=["항목 1", "항목 2", "항목 3"])),
        ]
        return SlideSchema(
            meta=SlideMeta(title="발표 자료", template="generic",
                           language="ko", total_slides=len(slides)),
            slides=slides)
