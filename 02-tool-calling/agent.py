import json
import os

import dotenv
from openai import OpenAI

from tools import TOOL_FUNCS, TOOLS

dotenv.load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com"
)

messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "今天北京和上海的温差是多少？"},
]

while True:
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        max_tokens=1024,
        temperature=0.2,
        stream=False,
        tools=TOOLS,
    )

    print(response)

    msg = response.choices[0].message

    if not msg.tool_calls:
        break

    messages.append(msg)

    for tc in msg.tool_calls:
        name = tc.function.name
        params = json.loads(tc.function.arguments)
        result = TOOL_FUNCS[name](**params)
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
