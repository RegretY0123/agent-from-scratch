import openai


def test_chat_ok(client, fake_client):
    r = client.post("/v1/chat", json={"message": "你好"})
    assert r.status_code == 200
    body = r.json()
    assert body["finished"] is True
    assert body["answer"] == "假回答"
    assert body["abort_reason"] is None


def test_validation_error(client):
    r = client.post("/v1/chat", json={})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_upstream_error(client, fake_client):
    def boom(**kwargs):
        raise openai.AuthenticationError.__new__(openai.AuthenticationError)

    fake_client.chat.completions.create = boom
    r = client.post("/v1/chat", json={"message": "你好"})
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "UPSTREAM_AUTH_FAILED"
    assert "9934" not in r.text


def test_missing_message_length(client):
    r = client.post("/v1/chat", json={"message": ""})
    assert r.status_code == 422
