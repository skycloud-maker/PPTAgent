# ARCHITECTURE.md
> PPT Agent — 시스템 아키텍처 문서  
> 최초 작성: 2026-04-02 | 상태: 초안(Draft)

---

## 1. 미션

> **자연어 요청 또는 데이터를 입력받아, 회사용 PPT(.pptx)를 자동으로 생성하는 AI Agent.**  
> 범용 비즈니스 장표와 템플릿 기반 반복 장표 두 가지 모드를 지원한다.

---

## 2. 전체 컴포넌트 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                      INPUT LAYER                        │
│  - 자연어 요청 (텍스트)                                    │
│  - 구조화 데이터 (CSV / JSON / Parquet)                   │
│  - 템플릿 지정 (템플릿 ID 또는 이름)                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    AI PLANNER                           │
│  - 입력을 분석하여 슬라이드 구조 설계                        │
│  - 출력: Slide Schema (JSON)                            │
│  - LLM 인터페이스로 추상화 → 교체 가능                      │
│    (현재: Claude API / 추후: 온프레미스 LLM 지원 예정)       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  TEMPLATE ENGINE                        │
│  - Slide Schema를 받아 레이아웃 결정                       │
│  - 슬라이드 타입별 레이아웃 매핑                             │
│    예: title / section / bullet / chart / table / blank │
│  - 템플릿 라이브러리에서 디자인 스타일 로드                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    RENDERER                             │
│  - python-pptx 기반 .pptx 파일 생성                      │
│  - 텍스트, 차트, 표, 이미지 등 요소 렌더링                   │
│  - 디자인 토큰(색상, 폰트, 여백) 일괄 적용                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                          │
│  - .pptx 파일 스트리밍 다운로드                            │
│  - 서버 저장 없음 (생성 후 즉시 메모리에서 제거)              │
│  - 다운로드 완료 후 임시 파일 삭제                           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Slide Schema 구조 (JSON)

AI Planner가 출력하는 중간 표현(Intermediate Representation).  
이 스키마가 시스템 전체의 핵심 계약(Contract)이다.

```json
{
  "meta": {
    "title": "2024 Q3 사업 현황",
    "template": "corporate-blue",
    "language": "ko",
    "total_slides": 8
  },
  "slides": [
    {
      "index": 1,
      "type": "title",
      "content": {
        "title": "2024 Q3 사업 현황",
        "subtitle": "전략기획팀 | 2024.10",
        "presenter": "홍길동"
      }
    },
    {
      "index": 2,
      "type": "bullet",
      "content": {
        "heading": "핵심 요약",
        "points": [
          "매출 전분기 대비 12% 성장",
          "신규 고객 확보 340건",
          "운영 비용 8% 절감"
        ]
      }
    },
    {
      "index": 3,
      "type": "chart",
      "content": {
        "heading": "월별 매출 추이",
        "chart_type": "bar",
        "data": {
          "labels": ["7월", "8월", "9월"],
          "series": [{ "name": "매출", "values": [120, 135, 142] }]
        }
      }
    }
  ]
}
```

**지원 슬라이드 타입:**

| type | 설명 |
|------|------|
| `title` | 표지 슬라이드 |
| `section` | 섹션 구분 슬라이드 |
| `bullet` | 텍스트 불릿 슬라이드 |
| `chart` | 차트 슬라이드 (bar / line / pie) |
| `table` | 표 슬라이드 |
| `two_column` | 2단 비교 슬라이드 |
| `image` | 이미지 중심 슬라이드 |
| `blank` | 빈 슬라이드 |

---

## 4. LLM 인터페이스 추상화

AI Planner는 특정 LLM에 종속되지 않도록 인터페이스로 분리한다.

```python
class LLMInterface:
    def plan_slides(self, user_request: str, data: dict | None) -> SlideSchema:
        raise NotImplementedError

class ClaudeAdapter(LLMInterface):
    # Claude API 사용
    ...

class LocalLLMAdapter(LLMInterface):
    # 온프레미스 LLM 사용 (추후 구현)
    ...
```

**교체 시나리오:**
- 현재: Claude API (외부)
- 추후: 사내 온프레미스 LLM으로 교체 → `LocalLLMAdapter`만 구현하면 나머지 파이프라인 변경 없음

---

## 5. 보안 원칙

### 5-1. 데이터 흐름 보안

| 구간 | 원칙 |
|------|------|
| 사용자 → 서버 | HTTPS 필수 |
| 서버 → LLM API | 입력 데이터 최소화 (요약/익명화 처리 옵션 제공 예정) |
| 서버 내부 | 생성된 파일은 메모리 또는 임시 디렉토리만 사용 |
| 서버 → 사용자 | 스트리밍 다운로드 후 임시 파일 즉시 삭제 |

### 5-2. 파일 생성 및 삭제 정책

- `.pptx` 파일은 디스크에 영구 저장하지 않는다.
- 생성 직후 Response stream으로 전달, 완료 후 `tempfile` 삭제.
- 로그에 파일 내용(슬라이드 텍스트 등)을 기록하지 않는다.

### 5-3. 추후 고려사항

- 온프레미스 LLM 전환 시 데이터가 외부로 나가지 않음
- 사내 인증(SSO/LDAP) 연동 옵션
- 감사 로그(Audit log): 누가 언제 어떤 템플릿으로 생성했는지 (내용 제외)

---

## 6. 운영 모드

### Mode A — 범용 생성 (Free-form)
사용자가 자유롭게 요청 → AI가 슬라이드 구조 전체 기획 → 생성

### Mode B — 템플릿 기반 반복 (Template-driven)
사전 정의된 템플릿 선택 → 데이터만 교체 → 빠른 생성  
예: 주간 보고, 월간 KPI 리뷰, 프로젝트 현황 보고

---

## 7. 확장 포인트

| 확장 항목 | 방법 |
|-----------|------|
| 새 템플릿 추가 | `templates/` 디렉토리에 템플릿 파일 + 메타데이터 추가 |
| 새 슬라이드 타입 추가 | Slide Schema에 type 추가 + Renderer에 렌더 함수 추가 |
| LLM 교체 | `LLMInterface` 구현체 교체 |
| 다국어 지원 | Slide Schema `language` 필드 + 폰트/레이아웃 분기 |
| VoC 데이터 연동 | Parquet 데이터 → Input Layer로 직접 주입 |
| 출력 포맷 추가 | Renderer에 PDF export 옵션 추가 (LibreOffice 변환) |

---

## 8. 미결 사항 (Open Questions)

> 설계하면서 아직 결정하지 못한 항목들. 추후 논의 후 업데이트.

- [ ] 프론트엔드 방식: 웹 UI vs CLI vs API-only?
- [ ] 템플릿 디자인 시스템: 자체 제작 vs 기존 회사 PPT 템플릿 추출?
- [ ] 온프레미스 LLM 전환 타임라인
- [ ] 사용자 인증 필요 여부 (내부 전용 vs 외부 공개)
- [ ] 차트 데이터 입력 방식: 파일 업로드 vs 직접 붙여넣기 vs API 연동?
