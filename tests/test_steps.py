FIRST = "/ai/v1/steps/first"
SHRINK = "/ai/v1/steps/shrink"
NEXT = "/ai/v1/steps/next"

BASE = {"goal": "과제 완료하기", "energy": 2, "burden": 4}


def test_health_needs_no_key(client):
    res = client.get("/ai/v1/health")
    assert res.status_code == 200
    assert res.json()["result"]["status"] == "UP"


def test_missing_key_is_401(client):
    res = client.post(FIRST, json=BASE)
    assert res.status_code == 401
    assert res.json()["code"] == "AI401"


def test_wrong_key_is_401(client):
    res = client.post(FIRST, json=BASE, headers={"X-Internal-Key": "nope"})
    assert res.status_code == 401


def test_validation_error_is_400_without_echoing_input(client, headers):
    res = client.post(FIRST, json={**BASE, "energy": 9, "goal": "비밀스러운 목표"}, headers=headers)
    body = res.json()
    assert res.status_code == 400
    assert body["code"] == "COMMON400_1"
    assert "비밀스러운 목표" not in body["message"]


def test_first_success(client, headers):
    res = client.post(FIRST, json=BASE, headers=headers)
    body = res.json()
    assert res.status_code == 200
    assert body["code"] == "COMMON200"
    assert body["result"]["isCrisis"] is False
    assert body["result"]["step"]
    assert res.headers["X-Request-Id"] == "test-req-1"


def test_first_crisis_keyword(client, headers):
    res = client.post(FIRST, json={**BASE, "goal": "다 끝내고 죽고 싶어"}, headers=headers)
    body = res.json()
    assert res.status_code == 200
    assert body["code"] == "CRISIS200"
    assert body["result"]["isCrisis"] is True
    assert body["result"]["step"] is None


def test_idiom_is_not_crisis(client, headers):
    res = client.post(FIRST, json={**BASE, "goal": "죽을 만큼 피곤한데 과제 해야 해"}, headers=headers)
    assert res.json()["code"] == "COMMON200"


def test_shrink_requires_fields(client, headers):
    res = client.post(SHRINK, json=BASE, headers=headers)
    assert res.status_code == 400
    assert res.json()["code"] == "COMMON400_1"


def test_shrink_success(client, headers):
    payload = {
        **BASE,
        "currentStep": "과제 자료 확인하기",
        "shrinkHistory": ["과제 자료 확인하기"],
        "shrinkCount": 1,
    }
    res = client.post(SHRINK, json=payload, headers=headers)
    body = res.json()
    assert res.status_code == 200
    assert body["result"]["step"] != "과제 자료 확인하기"


def test_shrink_count_limit_in_request(client, headers):
    payload = {**BASE, "currentStep": "a", "shrinkHistory": ["a"], "shrinkCount": 4}
    res = client.post(SHRINK, json=payload, headers=headers)
    assert res.status_code == 400


def test_next_success(client, headers):
    res = client.post(NEXT, json={**BASE, "currentStep": "노트북 켜기"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["result"]["step"]


def test_shrink_repeat_is_502(client, headers, monkeypatch):
    from app.llm import factory
    from app.llm.base import LlmStepOutput

    class Repeater:
        async def generate_step(self, request):
            return LlmStepOutput(is_crisis=False, step="과제 자료 확인하기!", can_shrink_more=True)

    app_llm = client.app.dependency_overrides
    from app.api import steps as steps_api

    app_llm[steps_api.get_llm] = lambda: Repeater()
    try:
        payload = {**BASE, "currentStep": "x", "shrinkHistory": ["과제 자료 확인하기"], "shrinkCount": 1}
        res = client.post(SHRINK, json=payload, headers=headers)
        assert res.status_code == 502
        assert res.json()["code"] == "AI502"
    finally:
        app_llm.clear()


def test_goal_over_50_chars_is_400(client, headers):
    res = client.post(FIRST, json={**BASE, "goal": "가" * 51}, headers=headers)
    assert res.status_code == 400
    assert res.json()["code"] == "COMMON400_1"


def test_first_has_reason(client, headers):
    result = client.post(FIRST, json=BASE, headers=headers).json()["result"]
    assert result["reason"]


def test_shrink_third_time_disables_more(client, headers):
    payload = {**BASE, "currentStep": "x", "shrinkHistory": ["a", "b"], "shrinkCount": 2}
    result = client.post(SHRINK, json=payload, headers=headers).json()["result"]
    assert result["canShrinkMore"] is False


def test_shrink_first_time_allows_more(client, headers):
    payload = {**BASE, "currentStep": "x", "shrinkHistory": [], "shrinkCount": 0}
    result = client.post(SHRINK, json=payload, headers=headers).json()["result"]
    assert result["canShrinkMore"] is True


FINISH = "/ai/v1/steps/finish-check"
FIN = {"goal": "방 청소하기", "currentStep": "바닥에 놓인 옷 1벌 줍기", "completedSteps": 3, "finishSuggested": False}


def _override_llm(client, llm):
    from app.api import steps as steps_api

    client.app.dependency_overrides[steps_api.get_llm] = lambda: llm


def test_finish_check_true_after_three_steps(client, headers):
    res = client.post(FINISH, json=FIN, headers=headers)
    assert res.status_code == 200
    assert res.json()["result"] == {"suggestFinish": True}


def test_finish_check_gated_without_calling_llm(client, headers):
    class Boom:
        async def generate_step(self, request):
            raise AssertionError("LLM must not be called")

    _override_llm(client, Boom())
    try:
        early = client.post(FINISH, json={**FIN, "completedSteps": 2}, headers=headers)
        again = client.post(FINISH, json={**FIN, "finishSuggested": True}, headers=headers)
    finally:
        client.app.dependency_overrides.clear()
    assert early.json()["result"]["suggestFinish"] is False
    assert again.json()["result"]["suggestFinish"] is False


def test_finish_check_degrades_to_false_on_llm_failure(client, headers):
    from app.llm.base import LlmUnavailableError

    class Down:
        async def generate_step(self, request):
            raise LlmUnavailableError("x")

    _override_llm(client, Down())
    try:
        res = client.post(FINISH, json=FIN, headers=headers)
    finally:
        client.app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()["result"]["suggestFinish"] is False


def test_finish_check_requires_key_and_fields(client, headers):
    assert client.post(FINISH, json=FIN).status_code == 401
    bad = {k: v for k, v in FIN.items() if k != "completedSteps"}
    assert client.post(FINISH, json=bad, headers=headers).status_code == 400


def test_next_has_no_suggest_finish(client, headers):
    body = {**BASE, "currentStep": "노트북 켜기", "energyChange": "UP"}
    assert "suggestFinish" not in client.post(NEXT, json=body, headers=headers).json()["result"]


def test_next_rejects_unknown_energy_change(client, headers):
    res = client.post(NEXT, json={**BASE, "currentStep": "x", "energyChange": "MAYBE"}, headers=headers)
    assert res.status_code == 400


def test_trailing_period_is_stripped(client, headers):
    from app.api import steps as steps_api
    from app.llm.base import LlmStepOutput

    class Dotted:
        async def generate_step(self, request):
            return LlmStepOutput(step="노트북 켜기.", reason="이유")

    client.app.dependency_overrides[steps_api.get_llm] = lambda: Dotted()
    try:
        assert client.post(FIRST, json=BASE, headers=headers).json()["result"]["step"] == "노트북 켜기"
    finally:
        client.app.dependency_overrides.clear()
