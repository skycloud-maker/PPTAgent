"""Mock LLM provider - API 키 없이 테스트용 슬라이드 스키마를 반환한다."""

from __future__ import annotations

import logging

from core.llm.interface import LLMInterface
from core.schema import SlideContent, SlideMeta, SlideSchema, SlideType, Slide

logger = logging.getLogger(__name__)

# 템플릿별 Mock 데이터
_MOCK_DATA: dict[str, dict] = {
    "weekly_report": {
        "meta_title": "주간 업무 보고",
        "slides": [
            {"type": SlideType.TITLE, "content": {"title": "주간 업무 보고", "subtitle": "작성자 | 날짜", "presenter": "담당팀"}},
            {"type": SlideType.BULLET, "content": {"heading": "이번 주 주요 업무", "points": ["주요 업무 항목 1", "주요 업무 항목 2", "주요 업무 항목 3"]}},
            {"type": SlideType.BULLET, "content": {"heading": "다음 주 계획", "points": ["계획 항목 1", "계획 항목 2", "계획 항목 3"]}},
            {"type": SlideType.BULLET, "content": {"heading": "이슈 / 특이사항", "points": ["이슈 항목 1", "이슈 항목 2"]}},
        ],
    },
    "project_status": {
        "meta_title": "프로젝트 현황 보고",
        "slides": [
            {"type": SlideType.TITLE, "content": {"title": "프로젝트 현황 보고", "subtitle": "프로젝트명 | 기간", "presenter": "담당팀"}},
            {"type": SlideType.BULLET, "content": {"heading": "프로젝트 개요", "points": ["목표: 프로젝트 목표 요약", "기간: 시작일 ~ 종료일", "담당: 팀/담당자"]}},
            {"type": SlideType.BULLET, "content": {"heading": "진행 현황", "points": ["완료: 완료된 주요 항목", "진행 중: 현재 진행 항목", "예정: 다음 단계 항목"]}},
            {"type": SlideType.TWO_COLUMN, "content": {"heading": "리스크 & 대응방안", "left_title": "리스크", "right_title": "대응방안", "left_points": ["리스크 항목 1", "리스크 항목 2"], "right_points": ["대응 방안 1", "대응 방안 2"]}},
            {"type": SlideType.BULLET, "content": {"heading": "다음 단계", "points": ["다음 단계 항목 1", "다음 단계 항목 2"]}},
        ],
    },
    "proposal": {
        "meta_title": "신규 기획안 제안",
        "slides": [
            {"type": SlideType.TITLE, "content": {"title": "신규 기획안 제안", "subtitle": "제안 배경 및 목적", "presenter": "제안팀"}},
            {"type": SlideType.BULLET, "content": {"heading": "제안 배경 / 문제 정의", "points": ["현황 및 문제점 1", "현황 및 문제점 2", "해결이 필요한 이유"]}},
            {"type": SlideType.BULLET, "content": {"heading": "핵심 제안 내용", "points": ["제안 내용 1", "제안 내용 2", "제안 내용 3"]}},
            {"type": SlideType.TWO_COLUMN, "content": {"heading": "기대 효과", "left_title": "정량적 효과", "right_title": "정성적 효과", "left_points": ["효과 항목 1", "효과 항목 2"], "right_points": ["효과 항목 1", "효과 항목 2"]}},
            {"type": SlideType.BULLET, "content": {"heading": "실행 계획", "points": ["1단계: 계획 항목", "2단계: 계획 항목", "3단계: 계획 항목"]}},
        ],
    },
    "data_report": {
        "meta_title": "데이터 분석 리포트",
        "slides": [
            {"type": SlideType.TITLE, "content": {"title": "데이터 분석 리포트", "subtitle": "분석 기간 | 담당팀", "presenter": "분석팀"}},
            {"type": SlideType.BULLET, "content": {"heading": "분석 배경 및 목적", "points": ["분석 배경 항목 1", "분석 배경 항목 2", "분석 목적"]}},
            {"type": SlideType.CHART, "content": {"heading": "주요 지표 현황", "caption": "데이터 기준: 분석 기간"}},
            {"type": SlideType.BULLET, "content": {"heading": "핵심 인사이트", "points": ["인사이트 1", "인사이트 2", "인사이트 3"]}},
            {"type": SlideType.BULLET, "content": {"heading": "개선 방향", "points": ["개선 방향 1", "개선 방향 2", "개선 방향 3"]}},
        ],
    },
}

_DEFAULT_MOCK = {
    "meta_title": "발표 자료",
    "slides": [
        {"type": SlideType.TITLE, "content": {"title": "발표 자료", "subtitle": "내부 공유용", "presenter": "작성팀"}},
        {"type": SlideType.BULLET, "content": {"heading": "주요 내용", "points": ["항목 1", "항목 2", "항목 3"]}},
        {"type": SlideType.BULLET, "content": {"heading": "결론 및 다음 단계", "points": ["결론 1", "결론 2"]}},
    ],
}


class MockAdapter(LLMInterface):
    """
    API 키 없이 테스트용으로 사용하는 Mock LLM 어댑터.
    실제 LLM 호출 없이 템플릿별 샘플 SlideSchema를 반환한다.
    """

    def plan_slides(
        self,
        user_request: str,
        template: str,
        data: dict | None = None,
    ) -> SlideSchema:
        logger.info("Mock 모드로 슬라이드 구조 생성 | template=%s", template)

        mock = _MOCK_DATA.get(template, _DEFAULT_MOCK)

        slides = []
        for idx, slide_def in enumerate(mock["slides"], start=1):
            slides.append(
                Slide(
                    index=idx,
                    type=slide_def["type"],
                    content=SlideContent(**slide_def["content"]),
                )
            )

        return SlideSchema(
            meta=SlideMeta(
                title=mock["meta_title"],
                template=template,
                language="ko",
                total_slides=len(slides),
            ),
            slides=slides,
        )
