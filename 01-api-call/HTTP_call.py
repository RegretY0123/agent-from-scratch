import requests
import json
import os
import dotenv

dotenv.load_dotenv()

url = "https://api.deepseek.com/chat/completions"

payload = json.dumps({
  "messages": [
    {
      "content": "You are a helpful assistant",
      "role": "system"
    },
    {
      "content": "Hi",
      "role": "user"
    }
  ],
  "model": "deepseek-flash",
  "thinking": {
    "type": "enabled"
  },
  "reasoning_effort": "none",
  "max_tokens": 4096,
  "response_format": {
    "type": "text"
  },
  "stop": None,
  "stream": False,
  "stream_options": None,
  "temperature": 1,
  "top_p": 1,
  "tools": None,
  "tool_choice": "none",
  "logprobs": False,
  "top_logprobs": None
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': f'Bearer {os.environ["DEEPSEEK_API_KEY"]}'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(f"content为：{response.json()['choices'][0]['message']['content']}")
print(f"reasoning_content为：{response.json()['choices'][0]['message']['reasoning_content']}")
print(f"输入token数为:{response.json()["usage"]["prompt_tokens"]},输出总token数为:{response.json()["usage"]["completion_tokens"]},其中思考token数为:{response.json()["usage"]["completion_tokens_details"]["reasoning_tokens"]},总token数为:{response.json()["usage"]["total_tokens"]},缓存命中为:{response.json()["usage"]["prompt_cache_hit_tokens"]},")