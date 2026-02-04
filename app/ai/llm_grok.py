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


def parse_message_2(message: str) -> dict:
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


def parse_message(message: str) -> dict:
    try:
        # ===== Current time VN =====
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        current_time = datetime.now(tz).isoformat()

        prompt = f"""
Bạn là AI chuyên TRÍCH XUẤT CÔNG VIỆC từ tin nhắn tiếng Việt.

========================
THỜI GIAN HỆ THỐNG

Thời gian hiện tại:
{current_time}

Múi giờ mặc định:
Asia/Ho_Chi_Minh (UTC+7)

========================
NHIỆM VỤ DUY NHẤT

1. Xác định tin nhắn CÓ PHẢI là công việc hay KHÔNG
2. Nếu CÓ → trích xuất đúng schema JSON

========================
QUY TẮC CỨNG (KHÔNG ĐƯỢC VI PHẠM)

Nếu tin nhắn đồng thời có:

1. Có người được giao việc:
   - Xuất hiện dạng "@Tên"

2. Có thời gian trong tương lai:
   - Ví dụ: mai, chiều mai, sáng mai, tối mai, tuần sau, ngày, giờ

3. Có động từ hành động:
   - Ví dụ: làm, hoàn thành, xử lý, đi, gặp, chuẩn bị, gửi, kiểm tra, họp, cập nhật

👉 CHỈ CẦN ĐỦ CẢ 3 ĐIỀU KIỆN
👉 BẮT BUỘC is_task = true

========================
QUY TẮC XỬ LÝ THỜI GIAN

- Phải chuyển mọi thời gian sang ISO 8601
- Phải dựa trên THỜI GIAN HỆ THỐNG
- Phải dùng múi giờ Asia/Ho_Chi_Minh

QUY ƯỚC THỜI GIAN:

- sáng  → 09:00
- trưa  → 12:00
- chiều → 14:00
- tối   → 19:00

Nếu không xác định được giờ chính xác:
→ start_time = null

Nếu không có thời gian nhắc:
→ remind_time = null

========================
QUY TẮC TRÍCH XUẤT

title:
- Ngắn gọn
- Rõ hành động chính

description:
- Viết đầy đủ nội dung công việc

assignees:
- Lấy danh sách tên sau ký tự "@"
- Loại bỏ ký tự "@"

========================
KHÔNG ĐƯỢC

- Không giải thích
- Không thêm text ngoài JSON
- Không markdown
- Không comment

========================
Schema JSON (PHẢI ĐÚNG 100%)

{{
  "is_task": true | false,
  "title": "string",
  "description": "string",
  "assignees": ["string"],
  "start_time": "ISO datetime hoặc null",
  "remind_time": "ISO datetime hoặc null"
}}

========================
TIN NHẮN CẦN PHÂN TÍCH:
"{message}"
"""

        res = llm.invoke(prompt)
        raw = res.content.strip()

        data = extract_json(raw)

        # ===== Safe fallback nếu model trả lỗi =====
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
