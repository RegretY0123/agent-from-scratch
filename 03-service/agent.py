import json
import logging
import random
import time
from collections import Counter

import openai
from config import get_settings
from models import ChatResponse
from tools import TOOL_FUNCS, TOOLS

RETRYABLE_ERRORS = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)

logger = logging.getLogger(__name__)


def call_fingerprint(name: str, arguments: str) -> str:
    try:
        params = json.loads(arguments)
    except json.JSONDecodeError:
        return f"{name}:{arguments}"
    return f"{name}:{json.dumps(params, sort_keys=True, ensure_ascii=False)}"


def call_with_retry(func, *args, **kwargs):
    settings = get_settings()
    for attempt in range(1, settings.retry_max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except RETRYABLE_ERRORS as exc:
            if attempt == settings.retry_max_attempts:
                logger.error("已尝试%d次仍失败：%s", attempt, exc)
                raise
            delay = min(
                settings.retry_base_delay * (2 ** (attempt - 1)),
                settings.retry_max_delay,
            )
            delay += random.uniform(0, delay * 0.5)
            logger.warning(
                "第%d次尝试失败（%s），%.2f秒后重试", attempt, type(exc).__name__, delay
            )
            time.sleep(delay)


def run_agent(user_message, client, max_steps=10, repeat_limit=2):
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": user_message},
    ]

    seen = Counter()

    index = 1
    total_tokens = 0
    finished = False
    abort_reason = None

    while index <= max_steps:
        logger.info("当前为第%d轮，messages条数为%d", index, len(messages))
        response = call_with_retry(
            client.chat.completions.create,
            model="deepseek-flash",
            messages=messages,
            max_tokens=1024,
            temperature=0.2,
            stream=False,
            tools=TOOLS,
        )

        logger.info("收到响应，finish_reason为：%s", response.choices[0].finish_reason)

        msg = response.choices[0].message

        total_tokens += response.usage.total_tokens

        if not msg.tool_calls:
            finished = True
            logger.info(
                "轮次结束，本次总轮数为：%d，总token数为：%d", index, total_tokens
            )
            break
        index += 1

        messages.append(msg)
        logger.debug("本轮结束，token用量为：%d", response.usage.total_tokens)

        for tc in msg.tool_calls:
            name = tc.function.name
            fp = call_fingerprint(name, tc.function.arguments)
            seen[fp] += 1
            if seen[fp] > repeat_limit:
                abort_reason = f"检测到重复调用：{fp}已经出现{seen[fp]}次"
                logger.warning(abort_reason)
                break
            try:
                params = json.loads(tc.function.arguments)
                logger.info(
                    "收到tool_calls，tool名字为：%s，内容为：%s",
                    name,
                    tc.function.arguments,
                )
                result = TOOL_FUNCS[name](**params)
                logger.info("工具执行完成，tool名字为：%s，结果为：%s", name, result)
            except json.JSONDecodeError as exc:
                logger.warning("字典转化失败：%s", exc)
                result = f"字典转化失败：{type(exc).__name__}：{exc}"
            except Exception as exc:
                logger.warning("工具调用出现错误，问题为：%s", exc)
                result = f"工具执行失败：{type(exc).__name__}：{exc}"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        if abort_reason is not None:
            break

    if finished:
        answer = response.choices[0].message.content
    else:
        answer = None
        if abort_reason is None:
            abort_reason = f"达到最大轮次{max_steps}，请重试"

    return ChatResponse(
        answer=answer,
        finished=finished,
        steps=index,
        total_tokens=total_tokens,
        abort_reason=abort_reason,
    )


if __name__ == "__main__":
    from deps import get_llm_client
    from logging_setup import setup_logging

    setup_logging()

    client = get_llm_client()
    result = run_agent("北京上海温差多少", client=client)
    print(
        f"最终回答为：{result.answer}，轮数为：{result.steps}，token为：{result.total_tokens}"
    )
    result = run_agent("1+1等于几", client=client)
    print(
        f"最终回答为：{result.answer}，轮数为：{result.steps}，token为：{result.total_tokens}"
    )
