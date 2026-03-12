from time_parser import parse_time
from llm_grok import extract_task_info

print(parse_time("mai 14h30"))
print(parse_time("8h30 sáng mai"))
print(parse_time("trong 2 tiếng nữa"))
print(parse_time("30 phút nữa"))
print(parse_time("thứ 6"))
print(parse_time("tuần sau thứ 3"))

print(extract_task_info("@Nguyen 14h30 mai nộp báo cáo"))
