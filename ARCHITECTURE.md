# ARCHITECTURE.md

## 미션

사용자의 요청과 내부 업무 맥락을 바탕으로 회사 전용 발표자료를 자동 생성하는 AI Agent를 만든다. 현재 우선 범위는 내부 보고용 `.pptx` 생성이다.

## 시스템 구성

### 1. Input Layer
- Streamlit UI에서 템플릿과 텍스트 입력 수집
- 데이터 리포트 템플릿에서는 CSV/JSON 업로드 허용
- 업로드 데이터는 전체 본문이 아니라 컬럼/행 수 위주로 요약해 전달

### 2. Planner Layer
- `core.llm.interface.LLMInterface`를 공통 계약으로 사용
- 현재 기본 구현은 `ClaudeAdapter`
- 앱에서는 `core.llm.get_default_llm()`만 호출

### 3. Schema Layer
- LLM 응답은 반드시 `SlideSchema`로 검증
- 첫 슬라이드는 `title`
- 최대 15장 제한
- 메타 정보의 `total_slides`는 검증 후 자동 동기화

### 4. Renderer Layer
- `python-pptx` 기반 렌더링
- 회사 전용 헤더/푸터/기밀 라벨 적용
- 로컬 로고가 있으면 사용하고, 없으면 회사명 텍스트 표시
- 결과물은 메모리에서 bytes로 생성

### 5. Output Layer
- Streamlit에서 바로 다운로드 버튼 제공
- 서버 측 영구 저장 없음

## 현재 설계 원칙

- 범용성보다 회사 내부 템플릿 정합성을 우선
- 외부 브랜딩 자산 다운로드 금지
- LLM 호출은 팩토리 진입점 사용
- 업로드 데이터는 최소 요약만 LLM에 전달

## 추후 확장 포인트

- 회사별 테마 프리셋 추가
- 차트/표 실제 렌더링
- 로컬 LLM adapter 추가
- 편집 UI 및 리뷰 점수화 추가
