# SECURITY.md
> PPT Agent — 보안 정책 문서  
> 최초 작성: 2026-04-02 | 상태: 초안(Draft)

---

## 1. 이 문서의 목적

PPT Agent는 회사 내부 데이터를 다루는 도구다.  
이 문서는 데이터 유출, 파일 노출, 의도치 않은 로깅을 방지하기 위한 보안 원칙을 정의한다.  
**모든 개발 단위 실행 전 AI 에이전트는 이 문서를 확인해야 한다.**

---

## 2. 핵심 보안 원칙 3가지

> 1. **데이터는 외부로 최소한만 나간다**
> 2. **파일은 서버에 남지 않는다**
> 3. **내용은 로그에 기록되지 않는다**

---

## 3. 데이터 흐름 보안

### 3-1. 전송 구간별 원칙

| 구간 | 원칙 |
|------|------|
| 사용자 브라우저 → 서버 | HTTPS 필수 (Streamlit Cloud 기본 제공) |
| 서버 → Claude API | 입력 데이터 최소화 원칙 적용 (아래 참고) |
| 서버 → 사용자 브라우저 | 스트리밍 다운로드, 서버 미저장 |

### 3-2. Claude API 전송 데이터 최소화 원칙

- 장표 생성에 **필요한 내용만** API로 전송한다
- 개인 식별 정보(이름, 연락처 등)가 포함된 경우 사용자에게 주의 안내를 표시한다
- 향후 온프레미스 LLM 전환 시 이 구간의 외부 전송이 완전히 제거된다

### 3-3. 추후 고려 (Post-MVP)
- 민감 데이터 감지 기능: 입력값에 주민번호, 카드번호 패턴 등이 포함되면 경고
- 온프레미스 LLM 전환으로 데이터 외부 전송 제로화

---

## 4. 파일 생성 및 삭제 정책

### 원칙
- `.pptx` 파일은 **디스크에 영구 저장하지 않는다**
- 생성된 파일은 메모리 버퍼 또는 임시 파일로만 존재한다
- 사용자에게 전달 완료 후 즉시 삭제한다

### 구현 방식

```python
import tempfile
import os

# ✅ 올바른 방식 — tempfile 사용 후 즉시 삭제
with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
    tmp_path = tmp.name

try:
    # 파일 생성
    renderer.save(tmp_path)
    # 스트리밍 다운로드로 전달
    with open(tmp_path, "rb") as f:
        st.download_button("다운로드", f, file_name="output.pptx")
finally:
    # 반드시 삭제
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

# ❌ 금지 — 고정 경로에 저장
prs.save("outputs/result.pptx")  # 절대 금지
```

### 체크리스트
- [ ] `tempfile` 모듈 사용 여부 확인
- [ ] `finally` 블록에서 삭제 처리 여부 확인
- [ ] `outputs/` 또는 `static/` 디렉토리에 .pptx 저장 코드 없음 확인

---

## 5. 로깅 정책

### 기록해도 되는 것 ✅
- 요청 시각, 템플릿 종류, 슬라이드 수
- API 응답 시간, 토큰 사용량 (숫자만)
- 에러 타입, 스택 트레이스

### 절대 기록하면 안 되는 것 ❌
- 사용자가 입력한 텍스트 내용
- Claude API에 전송한 프롬프트 내용
- 생성된 슬라이드 텍스트 내용
- 업로드된 데이터 파일 내용

### 로그 작성 예시

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 올바른 로그
logger.info("슬라이드 생성 요청 수신 | template=weekly_report | slides=7")
logger.info("Claude API 응답 완료 | tokens=842 | elapsed=3.2s")
logger.error("파일 생성 실패 | error=RendererError | template=weekly_report")

# ❌ 금지 로그
logger.info(f"사용자 입력: {user_input}")        # 내용 기록 금지
logger.info(f"API 프롬프트: {prompt}")           # 프롬프트 기록 금지
logger.info(f"생성된 슬라이드: {slide_schema}")  # 슬라이드 내용 기록 금지
```

---

## 6. API 키 및 인증 정보 관리

### 원칙
- API 키는 절대 코드에 하드코딩하지 않는다
- `.env` 파일로 관리하고 `.gitignore`에 반드시 포함한다
- Streamlit Cloud 배포 시 Secrets 기능을 사용한다

### 환경변수 목록

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Claude API 인증 키 | `sk-ant-...` |

### .gitignore 필수 항목
```
.env
*.pptx
tmp/
__pycache__/
```

---

## 7. Streamlit 배포 보안

| 항목 | 설정 |
|------|------|
| 접근 제한 | Streamlit Cloud의 viewer 이메일 제한 기능으로 사내 인원만 접근 |
| HTTPS | Streamlit Cloud 기본 제공 |
| API 키 | Streamlit Cloud Secrets에 저장 (코드에 미포함) |

---

## 8. 보안 체크리스트 (배포 전 확인)

### 코드 레벨
- [ ] API 키 하드코딩 없음
- [ ] `.env`가 `.gitignore`에 포함됨
- [ ] 모든 파일 생성이 `tempfile` 사용
- [ ] 모든 임시 파일이 `finally`에서 삭제됨
- [ ] 로그에 사용자 입력 내용 없음
- [ ] 로그에 API 프롬프트 내용 없음

### 배포 레벨
- [ ] Streamlit Cloud Secrets에 API 키 등록
- [ ] 접근 가능 이메일 목록 설정
- [ ] HTTPS 동작 확인

---

## 9. 미결 사항 (Open Questions)

- [ ] 온프레미스 LLM 전환 타임라인 결정 시 이 문서 업데이트 필요
- [ ] 사내 SSO / 인증 연동 필요 여부 (현재는 Streamlit Cloud 이메일 제한으로 대체)
- [ ] 감사 로그(Audit log) 도입 여부: 누가 언제 어떤 템플릿으로 생성했는지 (내용 제외)
