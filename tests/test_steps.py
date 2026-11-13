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
    payload = {**BASE, "currentStep": "a", "shrinkHistory": ["a"], "shrinkCount": 6}
    res = client.post(SHRINK, json=payload, headers=headers)
    assert res.status_code == 400


def test_next_success(client, headers):
    res = client.post(NEXT, json={**BASE, "currentStep": "노트북 켜기"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["result"]["step"]
