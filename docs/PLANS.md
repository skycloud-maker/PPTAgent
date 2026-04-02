# PLANS.md

## 개발 원칙

- 현재 목표는 회사 내부 자료용 MVP 완성
- 범용 템플릿 엔진은 후속 단계로 미룸
- 문서, 코드, 평가 케이스를 같은 방향으로 유지

## 진행 현황

### Phase 1. Foundation
- [x] 프로젝트 구조 구성
- [x] `SlideSchema` 정의
- [x] Claude planner 연결
- [x] Streamlit 앱 뼈대 구성

### Phase 2. MVP 안정화
- [x] Step 1 템플릿 선택
- [x] Step 2 입력 폼
- [x] Step 3 슬라이드 구조 확인
- [x] Step 4 PPTX 생성 및 다운로드
- [x] LLM factory 진입점 정리
- [x] 회사 전용 렌더러 정리
- [x] 외부 로고 다운로드 제거

### Phase 3. Harness / Eval
- [x] 대표 입력 케이스 추가
- [x] 기대 구조 체크리스트 추가
- [x] 수동 평가 스크립트 추가

### Phase 4. Next
- [ ] 차트 실제 렌더링
- [ ] 표 실제 렌더링
- [ ] 회사별 테마 프리셋 분리
- [ ] 로컬 LLM adapter 추가
- [ ] 프롬프트/출력 자동 평가 도입
