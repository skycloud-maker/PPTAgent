"""Mock adapter for local testing without an API."""

from __future__ import annotations

import logging

from core.llm.interface import LLMInterface
from core.schema import Slide, SlideContent, SlideMeta, SlideSchema, SlideType
from core.template_packs import get_template_pack

logger = logging.getLogger(__name__)


class MockAdapter(LLMInterface):
    """Return deterministic template-pack-based decks."""

    def plan_slides(self, user_request: str, template: str, data: dict | None = None) -> SlideSchema:
        logger.info("MockAdapter planning slides | template=%s", template)
        fields = self._parse_fields(user_request)
        pack = get_template_pack(template)

        if template == "weekly_exec":
            return self._build_weekly(pack.id, fields)
        if template == "project_exec":
            return self._build_project(pack.id, fields)
        if template == "proposal_exec":
            return self._build_proposal(pack.id, fields)
        return self._build_fallback(pack.id, pack.name, pack.summary)

    def _parse_fields(self, user_request: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        current_key: str | None = None
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

    def _to_bullets(self, text: str, limit: int = 5) -> list[str]:
        items: list[str] = []
        for line in text.splitlines():
            cleaned = line.strip().lstrip("-*• ")
            if cleaned:
                items.append(cleaned)
        return items[:limit]

    def _build_weekly(self, pack_id: str, fields: dict[str, str]) -> SlideSchema:
        period = fields.get("보고 기간", "이번 주")
        done = self._to_bullets(fields.get("완료 업무", ""))
        plan = self._to_bullets(fields.get("다음 계획", ""))
        issues = self._to_bullets(fields.get("이슈 및 특이사항", ""))
        reference = fields.get("참고할 긴 본문 또는 재료", "")

        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(title=f"{period} 주간보고", subtitle="HS본부 고객가치혁신실", presenter="PPTAgent", points=["이번 주 핵심 성과", "다음 주 실행 계획", "리스크 및 지원 요청"], caption="주간 의사결정 보고")),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(heading="핵심 요약", points=[done[0] if len(done) > 0 else "핵심 성과 1", done[1] if len(done) > 1 else "핵심 성과 2", plan[0] if len(plan) > 0 else "다음 단계 착수", issues[0] if len(issues) > 0 else "주요 리스크 관리 필요"], notes="첫 두 장 안에서 임원이 바로 판단할 수 있는 문구 중심")),
            Slide(index=3, type=SlideType.TABLE, content=SlideContent(heading="완료 업무 상세", data={"headers": ["구분", "주요 내용", "의미"], "rows": [["개발", done[0] if len(done) > 0 else "기본 구조 설계 완료", "기반 확보"], ["UI", done[1] if len(done) > 1 else "위자드 UI 구현", "사용 흐름 안정화"], ["기타", done[2] if len(done) > 2 else "브랜드 렌더 반영", "내부 공유 품질 개선"]]}, notes="세부 근거는 유첨으로 확장 가능")),
            Slide(index=4, type=SlideType.TWO_COLUMN, content=SlideContent(heading="다음 계획 및 리스크", left_title="다음 계획", right_title="리스크 / 지원", left_points=plan or ["내부 베타 테스트 진행", "기획 품질 보정"], right_points=issues or ["API 비용 검토 필요", "샘플 템플릿 추가 확보 필요"], notes="좌측은 실행, 우측은 지원요청 중심")),
            Slide(index=5, type=SlideType.CHART, content=SlideContent(heading="주요 진척도 추이", data={"categories": ["기획", "UI", "렌더", "LLM", "테스트"], "series": [{"name": "완료율", "values": [80, 95, 85, 65, 40]}]}, points=["UI/렌더 기반은 확보", "LLM 품질과 테스트 구간이 잔여 핵심 과제", "다음 주는 베타 검증 중심"], notes="참고 본문을 반영해 해석 포인트를 보강" if reference else "상대적으로 부족한 영역을 해석 포인트로 정리")),
            Slide(index=6, type=SlideType.BULLET, content=SlideContent(heading="결론 및 요청사항", points=["이번 주 내 핵심 구조 안정화 완료", "시범 사용자 피드백 확보 필요", "추가 템플릿 샘플 수집 요청"], notes="결론은 한 줄, 요청은 두세 개만 남기기")),
        ]
        return SlideSchema(meta=SlideMeta(title=f"{period} 주간보고", template=pack_id, language="ko", total_slides=len(slides)), slides=slides)

    def _build_project(self, pack_id: str, fields: dict[str, str]) -> SlideSchema:
        name = fields.get("프로젝트명", "프로젝트")
        goal = self._to_bullets(fields.get("프로젝트 목표", ""))
        progress = self._to_bullets(fields.get("진행 현황", ""))
        risks = self._to_bullets(fields.get("리스크 및 대응", ""))
        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(title=f"{name} 현황 보고", subtitle="프로젝트 의사결정 보고", presenter="PPTAgent", points=["목표", "진척", "리스크"])),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(heading="프로젝트 목표", points=goal or ["리드타임 단축", "품질 표준화", "사용성 확보"])),
            Slide(index=3, type=SlideType.CHART, content=SlideContent(heading="기능별 진척도", data={"categories": ["기획", "개발", "렌더", "검증"], "series": [{"name": "완료율", "values": [90, 80, 75, 45]}]}, points=progress or ["핵심 기능 구현 완료", "검증 단계 진입"])),
            Slide(index=4, type=SlideType.TABLE, content=SlideContent(heading="주요 작업 현황", data={"headers": ["영역", "상태", "설명"], "rows": [["UI", "완료", "위자드 UI 구현"], ["LLM", "진행", "품질 보정 중"], ["테스트", "진행", "시범 검증 준비"]]})),
            Slide(index=5, type=SlideType.TWO_COLUMN, content=SlideContent(heading="리스크 및 대응", left_title="리스크", right_title="대응 / 지원", left_points=risks or ["요구사항 확장", "비용 관리"], right_points=["템플릿 팩 우선 적용", "베타 범위 제한"])),
            Slide(index=6, type=SlideType.BULLET, content=SlideContent(heading="향후 일정 및 요청", points=["다음 주 검증 마무리", "내부 사용자 인터뷰 진행", "결정 필요 항목 정리"])),
        ]
        return SlideSchema(meta=SlideMeta(title=f"{name} 현황 보고", template=pack_id, language="ko", total_slides=len(slides)), slides=slides)

    def _build_proposal(self, pack_id: str, fields: dict[str, str]) -> SlideSchema:
        background = self._to_bullets(fields.get("배경 및 문제 정의", ""))
        solution = self._to_bullets(fields.get("해결 방안", ""))
        effect = self._to_bullets(fields.get("기대 효과", ""))
        slides = [
            Slide(index=1, type=SlideType.TITLE, content=SlideContent(title="기획 제안", subtitle="내부 개선안 보고", presenter="PPTAgent", points=["문제 정의", "제안안", "기대 효과"])),
            Slide(index=2, type=SlideType.BULLET, content=SlideContent(heading="배경과 문제 정의", points=background or ["반복 작업 증가", "품질 편차 발생"])),
            Slide(index=3, type=SlideType.TWO_COLUMN, content=SlideContent(heading="현행 vs 제안안", left_title="현행", right_title="제안안", left_points=["수작업 중심", "검토 라운드 길음"], right_points=solution or ["템플릿 기반 자동화", "수정 중심 협업"])),
            Slide(index=4, type=SlideType.TABLE, content=SlideContent(heading="기대 효과", data={"headers": ["항목", "효과", "측정 기준"], "rows": [["시간", effect[0] if len(effect) > 0 else "작성 시간 단축", "평균 소요시간"], ["품질", effect[1] if len(effect) > 1 else "문구 품질 표준화", "수정 횟수"]]})),
            Slide(index=5, type=SlideType.BULLET, content=SlideContent(heading="실행 계획", points=["MVP 적용", "샘플 템플릿 정비", "베타 운영"])),
            Slide(index=6, type=SlideType.BULLET, content=SlideContent(heading="결론 및 요청", points=["파일럿 승인 요청", "샘플 데이터 제공 요청"])),
        ]
        return SlideSchema(meta=SlideMeta(title="기획 제안", template=pack_id, language="ko", total_slides=len(slides)), slides=slides)

    def _build_fallback(self, pack_id: str, name: str, summary: str) -> SlideSchema:
        slides = [Slide(index=1, type=SlideType.TITLE, content=SlideContent(title=name, subtitle=summary, presenter="PPTAgent"))]
        return SlideSchema(meta=SlideMeta(title=name, template=pack_id, language="ko", total_slides=1), slides=slides)