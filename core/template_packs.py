"""Template pack definitions for PPTAgent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SlideBlueprint:
    key: str
    type: str
    title: str
    objective: str
    guidance: str


@dataclass(frozen=True)
class TemplatePack:
    id: str
    name: str
    icon: str
    summary: str
    recommended_for: str
    required_fields: tuple[str, ...]
    slides: tuple[SlideBlueprint, ...]


TEMPLATE_PACKS: dict[str, TemplatePack] = {
    "weekly_exec": TemplatePack(
        id="weekly_exec",
        name="주간 임원보고",
        icon="🧭",
        summary="주간 성과, 다음 계획, 리스크를 짧고 강하게 정리하는 6장 보고 팩",
        recommended_for="팀장/파트장/실무리더가 임원 또는 조직장에게 주간 단위 의사결정 보고",
        required_fields=("period", "done", "plan"),
        slides=(
            SlideBlueprint("cover", "title", "주간보고", "보고 제목과 핵심 메시지 제시", "표지는 제목, 보고주체, 핵심 메시지 3줄만 유지"),
            SlideBlueprint("summary", "bullet", "핵심 요약", "이번 주 핵심 성과를 두괄식으로 요약", "읽는 즉시 무엇이 완료되었고 왜 중요한지 보이게 작성"),
            SlideBlueprint("done_table", "table", "완료 업무 상세", "완료 업무를 구조화해 성과 중심으로 정리", "구분/주요 내용/성과 또는 의미 3열 권장"),
            SlideBlueprint("plan_risk", "two_column", "다음 계획 및 리스크", "실행계획과 리스크를 분리해 제시", "좌측은 계획, 우측은 리스크·지원요청 중심"),
            SlideBlueprint("progress_chart", "chart", "주요 진척도 추이", "기능 또는 과제 진척도를 시각화", "차트 오른쪽에 해석 포인트 2~3개 배치"),
            SlideBlueprint("closing", "bullet", "결론 및 요청사항", "한 줄 결론과 필요한 요청사항 정리", "최종 의사결정 포인트가 남도록 마무리"),
        ),
    ),
    "project_exec": TemplatePack(
        id="project_exec",
        name="프로젝트 현황보고",
        icon="🚀",
        summary="프로젝트 목표, 진척, 이슈, 의사결정 포인트를 정리하는 6장 팩",
        recommended_for="프로젝트 PM/PL이 조직장 또는 유관부서 리더에게 상태 공유",
        required_fields=("project_name", "goal", "progress"),
        slides=(
            SlideBlueprint("cover", "title", "프로젝트 현황 보고", "프로젝트와 보고 목적 소개", "표지에는 범위와 보고 목적만 간결하게"),
            SlideBlueprint("goal", "bullet", "프로젝트 목표", "왜 하는 프로젝트인지 두괄식 제시", "성과 기준과 기대효과를 먼저 보여주기"),
            SlideBlueprint("progress", "chart", "기능별 진척도", "영역별 완료 수준 시각화", "완료/지연 영역이 바로 보이게"),
            SlideBlueprint("status_table", "table", "주요 작업 현황", "작업별 상태와 이슈 구조화", "영역/상태/설명 3열 권장"),
            SlideBlueprint("risk_action", "two_column", "리스크 및 대응", "리스크와 대응계획 분리", "우측은 지원요청 또는 의사결정 항목 포함"),
            SlideBlueprint("closing", "bullet", "향후 일정 및 요청", "다음 단계와 요청사항 제시", "결정이 필요한 항목을 마지막에 명확히"),
        ),
    ),
    "proposal_exec": TemplatePack(
        id="proposal_exec",
        name="기획 제안보고",
        icon="💡",
        summary="문제 정의, 제안안, 기대효과, 실행계획을 설득형으로 정리하는 6장 팩",
        recommended_for="기획/전략/혁신 조직이 신규 과제나 개선안을 제안",
        required_fields=("background", "solution", "effect"),
        slides=(
            SlideBlueprint("cover", "title", "기획 제안", "제안 제목과 핵심 방향 소개", "표지에서 왜 필요한 제안인지 암시"),
            SlideBlueprint("problem", "bullet", "배경과 문제 정의", "현재 문제를 짧고 강하게 설명", "문제의 비용 또는 비효율이 드러나게"),
            SlideBlueprint("compare", "two_column", "현행 vs 제안안", "현재 방식과 제안 방안을 비교", "비교로 변화 포인트를 선명하게"),
            SlideBlueprint("effect_table", "table", "기대 효과", "효과와 측정 기준 구조화", "항목/효과/측정 기준 3열 권장"),
            SlideBlueprint("roadmap", "bullet", "실행 계획", "도입/실행 로드맵 정리", "바로 실행 가능한 단계로 분해"),
            SlideBlueprint("closing", "bullet", "결론 및 요청", "승인/지원 요청 정리", "결정 포인트를 마지막에 남기기"),
        ),
    ),
}


def list_template_packs() -> list[TemplatePack]:
    return list(TEMPLATE_PACKS.values())


def get_template_pack(pack_id: str) -> TemplatePack:
    return TEMPLATE_PACKS[pack_id]


def pack_to_prompt_dict(pack_id: str) -> dict[str, Any]:
    pack = get_template_pack(pack_id)
    return {
        "id": pack.id,
        "name": pack.name,
        "summary": pack.summary,
        "recommended_for": pack.recommended_for,
        "required_fields": list(pack.required_fields),
        "slides": [
            {
                "key": slide.key,
                "type": slide.type,
                "title": slide.title,
                "objective": slide.objective,
                "guidance": slide.guidance,
            }
            for slide in pack.slides
        ],
    }