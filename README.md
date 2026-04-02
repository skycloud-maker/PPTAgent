# PPTAgent

회사 내부 발표 자료 작성을 위한 AI PPT 생성 에이전트입니다. 현재 MVP는 회사 전용 템플릿 기반의 보고서와 기획서 생성을 우선 목표로 합니다.

## 현재 상태

- Streamlit 4단계 생성 흐름 구현
- OpenAI 기반 슬라이드 기획
- Pydantic `SlideSchema` 검증
- `python-pptx` 기반 회사 전용 템플릿 렌더링
- harness/eval용 샘플 케이스 추가

## 빠른 시작

### 1. 환경 변수 설정

```bat
copy .env.example .env
```

`.env`에 최소한 아래 값을 채워주세요.

- `OPENAI_API_KEY`
- 필요 시 `PPTAGENT_COMPANY_NAME`
- 필요 시 `PPTAGENT_LOGO_PATH`

### 2. 더블클릭 실행

앱 실행:

```bat
run_app.bat
```

Harness 케이스 확인:

```bat
run_harness.bat
```

배치 파일이 자동으로 다음을 수행합니다.

- `C:\codex\python312\python.exe` 사용
- 필요한 패키지 설치
- Streamlit 앱 또는 harness 실행

## 수동 실행

```bat
C:\codex\python312\python.exe -m pip install -r requirements.txt
C:\codex\python312\python.exe -m streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## 프로젝트 구조

```text
PPTAgent/
├── app.py
├── requirements.txt
├── run_app.bat
├── run_harness.bat
├── core/
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── interface.py
│   │   ├── openai.py
│   │   └── claude.py
│   ├── prompts/
│   │   └── slide_planner.py
│   ├── renderer.py
│   └── schema.py
├── docs/
├── harness/
│   ├── cases/
│   ├── expected/
│   └── run_manual_eval.py
├── .env.example
└── pyproject.toml
```

## 회사 전용 템플릿 방향

이 프로젝트는 장기적으로 범용화할 수 있지만, 현재 우선순위는 회사 내부 보고 자료 생성입니다.

- 외부 브랜드 다운로드에 의존하지 않음
- 로고는 로컬 경로나 미설정 상태를 지원
- 헤더, 푸터, 기밀 문구가 포함된 내부 문서 톤 유지
- 주간보고, 프로젝트 현황, 제안서, 데이터 리포트 중심 설계

## Harness / Eval

`harness/` 아래에 샘플 입력과 검토 기준을 추가했습니다.

```bat
run_harness.bat
```

API 키가 없는 상태에서도 케이스와 검토 포인트를 확인할 수 있습니다.