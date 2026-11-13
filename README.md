# Team28 AI Server

무기력한 사람을 위한 초소형 행동 지원 서비스의 AI 서버 (Python / FastAPI).
백엔드(Spring)가 내부 API로 호출하며, 프론트는 직접 호출하지 않습니다.

## 실행

Python 3.11 권장 (3.15 등 너무 새로운 버전은 패키지 호환 문제가 날 수 있음)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # AI_INTERNAL_KEY 등 값 확인
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/ai/v1/health
- 테스트: `pytest`

## 환경변수

| 이름 | 설명 |
| --- | --- |
| `AI_INTERNAL_KEY` | 백엔드가 `X-Internal-Key`로 보내는 값. 비어 있으면 모든 요청 401 |
| `LLM_PROVIDER` | `mock`(키 없이 가짜 응답) / `gemini` / `upstage` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | `gemini`일 때 필요. 모델명은 현재 제공되는 값으로 확인 |
| `UPSTAGE_API_KEY`, `UPSTAGE_MODEL`, `UPSTAGE_BASE_URL` | `upstage`일 때 필요. 기본 모델 `solar-pro4`, 기본 주소 `https://api.upstage.ai/v1` |
| `LLM_TIMEOUT_SECONDS` | LLM 응답 제한 시간. 초과하면 AI504 |
| `STEP_MAX_LENGTH` | step 최대 글자 수 |

## 엔드포인트 (`/ai/v1`)

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/steps/first` | 목표 입력의 위기 확인 + 첫 행동 |
| POST | `/steps/shrink` | 더 작은 행동 |
| POST | `/steps/next` | 다음 행동 |
| GET | `/health` | 헬스체크 (내부 키 불필요) |

## 구조

```
app/
  api/        엔드포인트 라우터
  schemas/    요청·응답 모델
  services/   기능별 로직 (위기 검사 -> LLM -> 검증)
  safety/     위기 키워드 검사 (공통 모듈)
  prompts/    프롬프트 텍스트 파일
  llm/        LLM 어댑터 (mock, gemini, upstage)
  core/       설정, 인증, 에러 핸들러, request-id 미들웨어, 응답 형식
tests/
```

## 아직 결정되지 않은 것

- 에너지·부담 값의 방향 (현재 가정: energy 1=낮음~5=높음, burden 1=적음~5=매우 큼)
- `step` 최대 길이 (현재 60자), `recentTries` 개수 (현재 최대 10)
- 위기 키워드 목록은 시작용 초안이며, 테스트 세트와 검토로 보강 필요
- health를 내부 키 없이 열어 둔 것 (명세의 "모든 요청 키 필수"와 다름)
