import json
import logging
import os
import random
import time
from collections import Counter

import dotenv
import openai
from openai import OpenAI
from tools import TOOL_FUNCS, TOOLS

MAX_STEPS = 10
REPEAT_LIMIT = 2
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 20.0

RETRYABLE_ERRORS = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)

seen = Counter()

dotenv.load_dotenv()

_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def call_fingerprint(name: str, arguments: str) -> str:
    try:
        params = json.loads(arguments)
    except json.JSONDecodeError:
        return f"{name}:{arguments}"
    return f"{name}:{json.dumps(params, sort_keys=True, ensure_ascii=False)}"


def call_with_retry(func, *args, **kwargs):
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            return func(*args, **kwargs)
        except RETRYABLE_ERRORS as exc:
            if attempt == RETRY_MAX_ATTEMPTS:
                logger.error("已尝试%d次仍失败：%s", attempt, exc)
                raise
            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
            delay += random.uniform(0, delay * 0.5)
            logger.warning(
                "第%d次尝试失败（%s），%.2f秒后重试", attempt, type(exc).__name__, delay
            )
            time.sleep(delay)


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
    timeout=30.0,
    max_retries=0,
)

messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "今天北京和上海的温差是多少？"},
]

index = 1
total_tokens = 0
finished = False
abort_reason = None

while index <= MAX_STEPS:
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
        logger.info("轮次结束，本次总轮数为：%d，总token数为：%d", index, total_tokens)
        break
    index += 1

    messages.append(msg)
    logger.debug("本轮结束，token用量为：%d", response.usage.total_tokens)

    for tc in msg.tool_calls:
        name = tc.function.name
        fp = call_fingerprint(name, tc.function.arguments)
        seen[fp] += 1
        if seen[fp] > REPEAT_LIMIT:
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
        except json.JSONDecodeError as exa:
            logger.warning("字典转化失败：%s", exa)
            result = f"字典转化失败：{type(exa).__name__}：{exa}"
        except Exception as exc:
            logger.warning("工具调用出现错误，问题为：%s", exc)
            result = f"工具执行失败：{type(exc).__name__}：{exc}"
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    if abort_reason is not None:
        break

if finished:
    print(f"最终回答为：{response.choices[0].message.content}")
else:
    if abort_reason:
        print(f"任务终止，{abort_reason}")
    else:
        print(f"达到最大轮次{MAX_STEPS}，请重试")
