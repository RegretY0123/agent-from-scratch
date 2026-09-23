from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()

client=OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],base_url="https://api.deepseek.com")

response=client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {"role":"system","content":"You are a helpful assistant"},
        {"role":"user","content":"Hello"} ,
    ],
    max_tokens=1024,
    temperature=0.7,
    stream=False
)

print(response.choices[0].message.content)