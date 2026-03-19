from datetime import datetime
import pytz
import json
import re
from langchain_groq import ChatGroq
# from app.ai.prompt import PROMPT
# from app.ai.time_parser import parse_time

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
- có thời gian

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
OUTPUT JSON

{{
  "is_task": true | false,
  "title": "string",
  "description": "string",
  "assignees": ["string"],
  "time_text": "string hoặc null"
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

    return data


# ==============================
# STEP 2
# Convert time_text -> ISO datetime
# ==============================
def parse_time_with_llm(time_text: str):

    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now_dt = datetime.now(tz)

    current_time = now_dt.isoformat()
    current_date = now_dt.strftime("%Y-%m-%d")
    weekday = now_dt.strftime("%A")

    prompt = f"""
Bạn là AI chuyên CHUYỂN ĐỔI thời gian tiếng Việt sang ISO datetime.

========================
THỜI GIAN HỆ THỐNG

Current datetime:
{current_time}

Current date:
{current_date}

Current weekday:
{weekday}

Timezone:
Asia/Ho_Chi_Minh (UTC+7)

========================
INPUT TIME TEXT

"{time_text}"

========================
QUY TẮC

1. Convert sang ISO 8601
2. Phải dùng timezone +07:00
3. Kết quả phải là thời gian trong tương lai

========================
QUY TẮC GIỜ

"sáng"
→ giữ nguyên giờ

"chiều"
→ giờ + 12 nếu < 12

"tối"
→ giờ + 12

Ví dụ:

2 giờ chiều
→ 14:00

3 giờ chiều
→ 15:00

7 giờ tối
→ 19:00

Nếu chỉ có:

"3h"
→ hiểu là 15:00

========================
QUY TẮC NGÀY

"mai"
→ ngày tiếp theo

"tuần sau"
→ cùng thứ tuần sau

"thứ 6"
→ thứ 6 gần nhất trong tương lai

========================
OUTPUT JSON

{{
  "start_time": "ISO datetime hoặc null"
}}
"""

    res = llm.invoke(prompt)
    raw = res.content.strip()

    data = extract_json(raw)

    if not data:
        return None

    return data.get("start_time")


# ==============================
# MAIN FUNCTION
# ==============================
def parse_message(message: str):

    try:

        # STEP 1: extract task
        task = extract_task_info(message)

        if not task.get("is_task"):
            return {"is_task": False}

        start_time = None

        # STEP 2: parse time
        if task.get("time_text"):
            # start_time = parse_time_with_llm(task["time_text"])
            start_time = parse_time(task["time_text"])

        result = {
            "is_task": True,
            "title": task.get("title"),
            "description": task.get("description"),
            "assignees": task.get("assignees"),
            "start_time": start_time,
            "remind_time": None
        }

        return result

    except Exception as e:
        print("TASK PARSER ERROR:", e)
        return {"is_task": False}
