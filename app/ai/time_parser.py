from datetime import datetime
import re
from datetime import datetime, timedelta
import pytz

TZ = pytz.timezone("Asia/Ho_Chi_Minh")

WEEKDAY_MAP = {
    "thứ 2": 0, "t2": 0,
    "thứ 3": 1, "t3": 1,
    "thứ 4": 2, "t4": 2,
    "thứ 5": 3, "t5": 3,
    "thứ 6": 4, "t6": 4,
    "thứ 7": 5, "t7": 5,
    "chủ nhật": 6, "cn": 6
}

DAY_KEYWORDS = {
    "mai": 1,
    "ngày mai": 1,
    "hôm nay": 0,
    "today": 0
}


def now():
    return datetime.now(TZ)


# ==============================
# NORMALIZE TEXT
# ==============================

def normalize(text: str):

    text = text.lower().strip()

    text = text.replace("giờ", "h")
    text = text.replace(" ", " ")

    text = re.sub(r"\s+", " ", text)

    return text


# ==============================
# PARSE HOUR + MINUTE
# ==============================

def parse_time_of_day(text):

    patterns = [
        r"(\d{1,2})h(\d{1,2})",  # 8h30
        r"(\d{1,2}):(\d{1,2})",  # 8:30
        r"(\d{1,2})h",           # 8h
    ]

    for p in patterns:

        m = re.search(p, text)

        if m:

            hour = int(m.group(1))

            minute = 0

            if len(m.groups()) >= 2 and m.group(2):
                minute = int(m.group(2))

            if "chiều" in text or "tối" in text:

                if hour < 12:
                    hour += 12

            if "sáng" in text:

                if hour == 12:
                    hour = 0

            if hour <= 6 and not any(x in text for x in ["sáng", "am"]):
                hour += 12

            return hour, minute

    return None, None


# ==============================
# RELATIVE TIME
# ==============================


def parse_specific_date(text, base):
    patterns = [
        r"(\d{1,2})[\/\-](\d{1,2})",              # 30/3, 30-3
        r"(\d{1,2})\.(\d{1,2})",                 # 30.3
        r"(\d{1,2})\s*tháng\s*(\d{1,2})",        # 30 tháng 3
        r"(\d{1,2})\s*thang\s*(\d{1,2})",        # 30 thang 3 (không dấu)
    ]

    for pattern in patterns:
        m = re.search(pattern, text.lower())
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = base.year

            try:
                dt = base.replace(year=year, month=month, day=day)

                # nếu ngày đã qua → sang năm sau
                if dt < base:
                    dt = dt.replace(year=year + 1)

                return dt

            except ValueError:
                return None

    return None


def parse_relative(text):

    base = now()

    m = re.search(r"(\d+)\s*phút.*nữa", text)
    if m:
        return base + timedelta(minutes=int(m.group(1)))

    m = re.search(r"(\d+)\s*(giờ|tiếng).*nữa", text)
    if m:
        return base + timedelta(hours=int(m.group(1)))

    m = re.search(r"(\d+)\s*ngày.*nữa", text)
    if m:
        return base + timedelta(days=int(m.group(1)))

    return None


# ==============================
# DAY KEYWORD
# ==============================

def parse_day_keyword(text, base):

    for k, v in DAY_KEYWORDS.items():

        if k in text:
            return base + timedelta(days=v)

    return None


# ==============================
# WEEKDAY
# ==============================

def parse_weekday(text, base):

    for k, v in WEEKDAY_MAP.items():

        if k in text:

            today = base.weekday()

            days = v - today

            if days <= 0:
                days += 7

            return base + timedelta(days=days)

    return None


# ==============================
# NEXT WEEK
# ==============================

def parse_next_week(text, base):

    if "tuần sau" not in text:
        return None

    weekday = parse_weekday(text, base)

    if weekday:
        return weekday + timedelta(days=7)

    return base + timedelta(days=7)


# ==============================
# MONTH EDGE
# ==============================

def parse_month_edge(text, base):

    if "cuối tháng" in text:

        next_month = base.replace(day=28) + timedelta(days=4)

        last_day = next_month - timedelta(days=next_month.day)

        return last_day

    if "đầu tháng" in text:

        return base.replace(day=1) + timedelta(days=1)

    return None


# ==============================
# APPLY TIME
# ==============================

def apply_time(dt, hour, minute):

    if hour is None:
        hour = 9
        minute = 0

    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ==============================
# MAIN PARSER
# ==============================

def parse_time(text: str):

    if not text:
        return None

    text = normalize(text)

    base = now()

    hour, minute = parse_time_of_day(text)

    # ---------------------------
    # relative time
    # ---------------------------

    rel = parse_relative(text)

    if rel:
        return rel.isoformat()

    # ---------------------------
    # mai / hôm nay
    # ---------------------------

    day = parse_day_keyword(text, base)

    if day:

        dt = apply_time(day, hour, minute)

        return dt.isoformat()

    # ---------------------------
    # tuần sau
    # ---------------------------

    next_week = parse_next_week(text, base)

    if next_week:

        dt = apply_time(next_week, hour, minute)

        return dt.isoformat()

    # specific

    specific = parse_specific_date(text, base)

    if specific:
        dt = apply_time(specific, hour, minute)
        return dt.isoformat()
    # ---------------------------
    # weekday
    # ---------------------------

    weekday = parse_weekday(text, base)

    if weekday:

        dt = apply_time(weekday, hour, minute)

        return dt.isoformat()

    # ---------------------------
    # month edge
    # ---------------------------

    month = parse_month_edge(text, base)

    if month:

        dt = apply_time(month, hour, minute)

        return dt.isoformat()

    # ---------------------------
    # hour only
    # ---------------------------

    if hour is not None:

        dt = base.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if dt < base:
            dt += timedelta(days=1)

        return dt.isoformat()

    return None
