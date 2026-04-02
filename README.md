# PPTAgent

AI가 자연어 요청을 받아 회사용 PPT(.pptx)를 자동 생성하는 도구입니다.

## 빠른 시작

### 1. 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 클론 후
cd PPTAgent
uv sync
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 입력
```

### 3. 실행

```bash
uv run streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## 프로젝트 구조

```
PPTAgent/
├── app.py                  # Streamlit 진입점
├── core/
│   ├── schema.py           # SlideSchema (Pydantic)
│   ├── renderer.py         # python-pptx 렌더러
│   ├── llm/
│   │   ├── interface.py    # LLM 추상화 인터페이스
│   │   └── claude.py       # Claude API 어댑터
│   └── prompts/
│       └── slide_planner.py # 슬라이드 기획 프롬프트
├── templates/              # 템플릿 정의 (Phase 3)
├── docs/                   # 하네스 문서
├── .env.example
└── pyproject.toml
```

## 하네스 문서

이 프로젝트는 하네스 엔지니어링 방식으로 개발됩니다.  
AI와 작업할 때는 아래 3개 문서를 항상 첨부하세요:

- `AGENTS.md` — AI 행동 규칙
- `ARCHITECTURE.md` — 시스템 구조
- `docs/PLANS.md` — 현재 진행 상황

## 현재 개발 단계

- [x] Phase 1-A: 프로젝트 기본 구조 세팅
- [ ] Phase 2-A: Streamlit 앱 기본 구조 + 진행 바
- [ ] Phase 2-B ~ 2-F: MVP 핵심 기능
