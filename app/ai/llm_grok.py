import json
import re
from langchain_groq import ChatGroq
from app.ai.prompt import PROMPT

GROQ_API_KEY = "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"

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0,
)


def extract_json(text: str) -> dict:
    """
    LLM đôi khi trả thêm chữ → bóc JSON an toàn
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())


def parse_message_1(message: str) -> dict:
    try:
        prompt = PROMPT.format(message=message)

        # ⚠️ invoke() trả về AIMessage
        res = llm.invoke(prompt)

        raw = res.content.strip()

        return extract_json(raw)

    except Exception as e:
        print("GROQ LLM ERROR:", e)
        return {"is_task": False}


def parse_message(message: str) -> dict:
    try:
        prompt = f"""
Bạn là AI trích xuất công việc từ tin nhắn tiếng Việt.

LUẬT BẮT BUỘC:
- Nếu tin nhắn có nhắc tới người (@tên)
- VÀ có thời gian trong tương lai (mai, chiều mai, ngày, giờ)
- VÀ có hành động (làm, hoàn thành, đi, gặp, chuẩn bị, xử lý)
→ THÌ PHẢI coi là CÔNG VIỆC (is_task = true)

CHỈ TRẢ VỀ JSON. KHÔNG giải thích.

Schema:
{{
  "is_task": true | false,
  "title": "tiêu đề ngắn",
  "description": "mô tả đầy đủ",
  "assignees": ["Hung"],
  "start_time": "ISO datetime hoặc null",
  "remind_time": "ISO datetime hoặc null"
}}

Tin nhắn:
\"{message}\"
"""

        # Groq / LangChain
        res = llm.invoke(prompt)

        raw = res.content.strip()

        return extract_json(raw)

    except Exception as e:
        print("GROQ LLM ERROR:", e)
        return {"is_task": False}
