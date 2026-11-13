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
| `LLM_TIMEOUT_SECONDS` | LLM 응답 제한 시간(기본 6초). 초과하면 AI504 |
| `STEP_MAX_LENGTH` | step 최대 글자 수 |
| `SHRINK_MAX` | 같은 걸음에서 더 작게 최대 횟수 (기본 5, API 명세서 기준. Figma #4 는 3번이라 팀 확인 필요) |

## 엔드포인트 (`/ai/v1`)

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/steps/first` | 목표 입력의 위기 확인 + 첫 행동 |
| POST | `/steps/shrink` | 더 작은 행동 |
| POST | `/steps/next` | 다음 행동 |
| GET | `/health` | 헬스체크 (내부 키 불필요) |

## 요청·응답 요약 (Figma 확정 사항 반영)

- 요청 공통: `goal`(1~200자, 50자 제한은 백엔드가 검증), `energy`·`burden`(1~4), `recentTries`
- `/steps/shrink`: `currentStep`, `shrinkHistory`, `shrinkCount`(0~5), 선택값 `isLastStep`(줄이는 대상이 마지막 걸음이면 true, 결과에 그대로 이어짐). `SHRINK_MAX`(기본 5)번째 더 작게에서는 `canShrinkMore=false`
- `/steps/next`: `currentStep`, 선택값 `energyChange`(`SAME`/`UP`/`DOWN`), `completedSteps`(해본 걸음 수), `finishSuggested`(이미 마무리 제안한 목표인지)
- 응답 `result`: `isCrisis`, `step`("~하기" 구절, 마침표 없음), `canShrinkMore`, `reason`(이유 문구, 없으면 null), `isLastStep`(next에서 3걸음 이상·미제안일 때 AI가 판단, first는 항상 false)
- `reason`은 Figma 화면 기준으로 추가했고, AI 출력으로 할지는 팀 확인이 필요합니다.

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

- 에너지·부담 값 방향: 1~4이고, 에너지는 1=완전히 방전됨~4=꽤 괜찮아요, 부담은 1=너무 막막해요~4=해볼 만해요로 가정(Figma 라벨 순서). 백엔드·프론트 확인 필요
- `step` 최대 길이 (현재 60자), `recentTries` 개수 (현재 최대 10)
- 위기 키워드 목록은 시작용 초안이며, 테스트 세트와 검토로 보강 필요
- health를 내부 키 없이 열어 둔 것 (명세의 "모든 요청 키 필수"와 다름)
