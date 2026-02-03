from app.ai.prompt import PROMPT
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"  # đổi sang 3b để test trước


def parse_message(message: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": PROMPT.format(message=message)
            }
        ],
        "stream": False
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=120)

    # 🔥 DEBUG CỰC QUAN TRỌNG
    if res.status_code != 200:
        print("OLLAMA ERROR:", res.status_code, res.text)
        return {"is_task": False}

    data = res.json()

    try:
        raw = data["message"]["content"].strip()
        return json.loads(raw)
    except Exception as e:
        print("PARSE ERROR:", data)
        return {"is_task": False}
