from time_parser import parse_time
from llm_grok import extract_task_info, parse_message

print(parse_time("14h30 mai"))
print(parse_time("sáng mai 10h30"))

print(parse_message("3 ngày nữa nộp báo cáo nhé @Hung"))
