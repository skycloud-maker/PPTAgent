"""Prompt builder for template-pack-driven executive decks."""

from __future__ import annotations

import json

from core.template_packs import pack_to_prompt_dict

SLIDE_TYPES = ["title", "section", "bullet", "chart", "table", "two_column", "image", "blank"]


SYSTEM_PROMPT = """
당신은 LG전자 내부 보고자료를 기획하는 수석 프레젠테이션 전략가입니다.

목표:
- 사용자가 입력한 거친 메모를 임원/조직장 보고 수준의 장표 문구로 재구성합니다.
- 다만 장표 구조를 마음대로 새로 만들지 말고, 제공된 템플릿 팩의 슬라이드 순서와 타입을 최대한 유지합니다.
- 사용자는 큰 구조를 바꾸지 않고도 템플릿만으로 높은 완성도를 얻고 싶어 합니다.
- 당신의 역할은 템플릿 슬롯을 더 적합한 제목, bullet, table, chart, two_column 내용으로 채우는 것입니다.

좋은 보고 장표 기준:
1. 첫 1~2장은 읽는 즉시 핵심을 파악할 수 있어야 합니다.
2. 장표마다 메시지가 하나씩만 남아야 합니다.
3. 단순 작업 나열이 아니라 성과, 의미, 의사결정 포인트가 보여야 합니다.
4. 제목은 짧고 강하게, 20자 안팎으로 작성합니다.
5. bullet은 장표용 구/절 위주로 압축합니다.
6. table은 항목/내용/의미 구조가 드러나야 합니다.
7. chart는 차트 자체보다 해석 포인트가 중요합니다.
8. notes에는 상세 설명, 유첨으로 보낼 메모, 강조 지시만 넣습니다.
9. 결과물에는 사용자의 편집 지시문이나 placeholder 문구를 노출하지 않습니다.
10. 출력은 반드시 JSON만 제공합니다.

반드시 지킬 것:
- slide index는 템플릿 팩 순서를 유지합니다.
- slide type은 템플릿 팩 정의를 우선 따릅니다.
- 각 slide content는 해당 slide objective와 guidance에 맞게 채웁니다.
- title slide의 notes에는 내부 편집 메모를 넣지 않습니다.
""".strip()


def build_prompt(user_request: str, template: str, data: dict | None = None) -> str:
    pack = pack_to_prompt_dict(template)
    sections = [
        "[SYSTEM]",
        SYSTEM_PROMPT,
        "",
        "[TEMPLATE_PACK]",
        json.dumps(pack, ensure_ascii=False, indent=2),
        "",
        "[ALLOWED_SLIDE_TYPES]",
        ", ".join(SLIDE_TYPES),
        "",
        "[USER_INPUT]",
        user_request,
    ]

    if data:
        sections.extend(
            [
                "",
                "[UPLOADED_DATA_SUMMARY]",
                json.dumps(data, ensure_ascii=False, indent=2),
            ]
        )

    sections.extend(
        [
            "",
            "[OUTPUT_SCHEMA]",
            "meta.title에는 실제 보고서 제목을 넣고, slides는 템플릿 팩 slides 길이와 동일하게 유지하세요.",
            "각 slide.content에는 title/heading/points/data/left_points/right_points/notes 중 필요한 필드만 채우세요.",
            "table 슬라이드는 data.headers 와 data.rows를 채우세요.",
            "chart 슬라이드는 data.categories 와 data.series를 채우고, points에는 차트 해석 포인트를 넣으세요.",
            "two_column 슬라이드는 left_title/right_title/left_points/right_points를 채우세요.",
            "JSON 외의 설명은 출력하지 마세요.",
        ]
    )

    return "\n".join(sections)