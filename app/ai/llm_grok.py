import os
from datetime import datetime, timedelta
import pytz
import json
import re
from langchain_groq import ChatGroq
# from app.ai.prompt import PROMPT
from app.ai.time_parser import parse_time
# from time_parser import parse_time

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

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


# ==============================
# STEP 1
# Extract task info + time text
# ==============================
def extract_task_info(message: str):

    prompt = f"""
Bạn là AI chuyên TRÍCH XUẤT CÔNG VIỆC từ tin nhắn tiếng Việt.

========================
BƯỚC 1: CHUẨN HÓA TIN NHẮN

Sửa các lỗi chính tả nhẹ nếu có, ví dụ:

baos cáo → báo cáo
ngy mai → ngày mai
nop → nộp
baoca → báo cáo

Chỉ sửa lỗi chính tả phổ biến.
KHÔNG được thay đổi ý nghĩa câu.
KHÔNG được thay đổi định dạng thời gian.

Ví dụ:
"@Nguyen 8h30 sang mai nop baos cao"
→ "@Nguyen 8h30 sáng mai nộp báo cáo"

========================
BƯỚC 2: TRÍCH XUẤT TASK

NHIỆM VỤ:

1. Xác định có phải công việc hay không
2. Trích xuất thông tin task
3. Lấy CHÍNH XÁC cụm thời gian

========================
QUY TẮC TASK

is_task = true nếu có:
- @Tên
- có hành động

KHÔNG phụ thuộc vào việc có thời gian hay không.

Ngay cả khi KHÔNG có thời gian → vẫn là task.

Thời gian:
- Có thể có hoặc KHÔNG
- Nếu không có → time_text = null

assignees:
- lấy tên sau ký tự @

========================
QUY TẮC TIME_TEXT (RẤT QUAN TRỌNG)

time_text phải là **toàn bộ cụm thời gian liên tục trong câu**.

KHÔNG được bỏ phần giờ/phút.

Nếu có:
- giờ
- phút
- buổi (sáng/chiều/tối)
- ngày (mai, thứ 6, tuần sau)

→ phải lấy TẤT CẢ.

Luôn lấy **cụm thời gian dài nhất**.

========================
VÍ DỤ

Input:
"@Nguyen 8h30 sáng mai nộp báo cáo"

Output:
"time_text": "8h30 sáng mai"


Input:
"@Lan t6 9h nop file"

Output:
"time_text": "t6 9h"


Input:
"@Minh 30 phut nua goi khach"

Output:
"time_text": "30 phút nữa"

========================
KHÔNG được:
- convert thời gian
- suy luận giờ
- cắt bớt cụm thời gian

Chỉ COPY nguyên văn cụm thời gian từ câu đã chuẩn hóa.

========================
QUY TẮC THỜI GIAN MẶC ĐỊNH

Nếu KHÔNG tìm thấy cụm thời gian trong câu:
→ time_text = null

KHÔNG được tự suy luận hoặc tự thêm thời gian.

========================
OUTPUT JSON

{{
  "is_task": true | false,
  "title": "string",
  "description": "string",
  "assignees": ["string"],
  "time_text": "string hoặc null"
}}

========================
VÍ DỤ KHÔNG CÓ THỜI GIAN

Input:
"@Nguyen nộp báo cáo"

Output:
{{
  "is_task": true,
  "title": "nộp báo cáo",
  "description": "nộp báo cáo",
  "assignees": ["Nguyen"],
  "time_text": null
}}

Input:
"@Lan gửi file thiết kế"

Output:
{{
  "is_task": true,
  "title": "gửi file thiết kế",
  "description": "gửi file thiết kế",
  "assignees": ["Lan"],
  "time_text": null
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

    data.setdefault("is_task", False)
    data.setdefault("title", "")
    data.setdefault("description", "")
    data.setdefault("assignees", [])
    data.setdefault("time_text", None)

    if data.get("is_task") and not data.get("time_text"):
        data["time_text"] = "5 phút nữa"

    return data

# ==============================
# MAIN FUNCTION
# ==============================


def extract_assignees_regex(text: str):
    # Lấy tất cả chuỗi sau @, dừng ở space hoặc ký tự đặc biệt
    # matches = re.findall(r"@([^\s@]+)", text)
    matches = re.findall(r"@([^\s@,\.!?:;]+)", text)

    # Optional: remove duplicate
    return list(dict.fromkeys(matches))


def parse_message(message: str):

    try:
        # STEP 1: extract task
        task = extract_task_info(message)

        if not task.get("is_task"):
            return {"is_task": False}

        start_time = None

        # STEP 2: parse time
        if task.get("time_text"):
            start_time = parse_time(task["time_text"])
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)

            if start_time:
                remind_time = start_time - timedelta(minutes=5)

        # 👇 clean assignees tại đây
        assignees = extract_assignees_regex(message)
        # assignees = clean_assignees(task.get("assignees"))

        result = {
            "is_task": True,
            "title": task.get("title"),
            # "description": task.get("description"),
            "description": message,
            "assignees": assignees,
            "start_time": start_time,
            "remind_time": remind_time
        }

        return result

    except Exception as e:
        print("TASK PARSER ERROR:", e)
        return {"is_task": False}
