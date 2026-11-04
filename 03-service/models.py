from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(
        description="用户的问题，不能为空",
        min_length=1,
        max_length=2000,
    )


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str | None = Field(
        default=None, description="Agent的回答，未正常完成时为None"
    )
    finished: bool = Field(
        description="是否正常完成。false时answer为null，看abort_reason"
    )
    steps: int = Field(description="实际执行的轮数", ge=0)
    total_tokens: int = Field(default=0, description="本次累计消耗的token数", ge=0)
    abort_reason: str | None = Field(
        default=None, description="终止原因，正常完成时为null"
    )


if __name__ == "__main__":
    from pydantic import ValidationError

    req = ChatRequest(message="北京上海温差多少")
    assert req.message == "北京上海温差多少"
    assert isinstance(req.message, str)

    try:
        ChatRequest()
        raise AssertionError("缺message时应该报错，但未报错")
    except ValidationError as e:
        assert e.errors()[0]["type"] == "missing"

    try:
        ChatRequest(message="")
        raise AssertionError("空字符串应该被拒绝，但没有")
    except ValidationError as e:
        assert e.errors()[0]["type"] == "string_too_short"

    ok = ChatResponse(
        answer="北京比上海低3度", finished=True, steps=3, total_tokens=1234
    )
    assert ok.answer == "北京比上海低3度"
    assert ok.abort_reason is None

    bad = ChatResponse(finished=False, steps=3, abort_reason="检测到重复调用")
    assert bad.answer is None
    assert bad.total_tokens == 0

    try:
        ChatResponse()
        raise AssertionError("finished/steps为必填项，应该报错")
    except ValidationError as e:
        assert {x["loc"][0] for x in e.errors()} == {"finished", "steps"}

    print("models.py测试全部通过")
