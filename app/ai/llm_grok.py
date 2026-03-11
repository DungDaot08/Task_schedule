from datetime import datetime
import pytz
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


def parse_message(message: str) -> dict:
    try:
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        now_dt = datetime.now(tz)
        current_time = now_dt.isoformat()
        current_date = now_dt.strftime("%Y-%m-%d")
        current_weekday = now_dt.strftime("%A")

        prompt = f"""
Bạn là AI chuyên TRÍCH XUẤT CÔNG VIỆC từ tin nhắn tiếng Việt.

========================
THỜI GIAN HỆ THỐNG

Current datetime:
{current_time}

Current date:
{current_date}

Current weekday:
{current_weekday}

Timezone:
Asia/Ho_Chi_Minh (UTC+7)

========================
NHIỆM VỤ

1. Xác định có phải công việc hay không
2. Nếu có → xuất JSON đúng schema

========================
QUY TẮC CỨNG

Nếu tin nhắn có đủ:
- Có @Tên
- Có thời gian tương lai
- Có động từ hành động

👉 is_task = true

========================
QUY TẮC XỬ LÝ THỜI GIAN (BẮT BUỘC)

1. Tất cả thời gian phải convert sang ISO 8601
2. Phải dùng timezone Asia/Ho_Chi_Minh
3. Thời gian kết quả LUÔN phải nằm trong tương lai so với Current datetime

⚠️ Nếu thời gian suy ra nhỏ hơn hoặc bằng Current datetime:
→ Phải chuyển sang ngày gần nhất trong tương lai

========================
QUY ƯỚC BUỔI

- sáng = 09:00
- trưa = 12:00
- chiều = 14:00
- tối = 19:00

========================
QUY TẮC SUY LUẬN

"3h chiều"
→ Nếu đã qua 15:00 hôm nay → chuyển sang ngày mai 15:00

"3h"
→ hiểu là 15:00

"mai"
→ ngày tiếp theo

"tuần sau"
→ cùng thứ của tuần kế tiếp

========================
Nếu không xác định được giờ:
→ start_time = null

Nếu không có nhắc:
→ remind_time = null

========================
QUY TẮC TRÍCH XUẤT

title:
- Ngắn gọn
- Rõ hành động

description:
- Viết đầy đủ nội dung

assignees:
- Lấy tên sau @

========================
KHÔNG ĐƯỢC

- Không giải thích
- Không text ngoài JSON

========================
Schema JSON

{{
  "is_task": true | false,
  "title": "string",
  "description": "string",
  "assignees": ["string"],
  "start_time": "ISO datetime",
  "remind_time": "ISO datetime"
}}

========================
TIN NHẮN:
"{message}"
"""

        res = llm.invoke(prompt)
        raw = res.content.strip()

        data = extract_json(raw)

        if not isinstance(data, dict):
            return {"is_task": False}

        # đảm bảo đủ key
        data.setdefault("is_task", False)
        data.setdefault("title", "")
        data.setdefault("description", "")
        data.setdefault("assignees", [])
        data.setdefault("start_time", None)
        data.setdefault("remind_time", None)

        return data

    except Exception as e:
        print("GROQ LLM ERROR:", e)
        return {"is_task": False}
