from time_parser import parse_time
from llm_grok import extract_task_info, parse_message

print(parse_time("14h30 mai"))
print(parse_time("sáng mai 10h30"))

print(parse_message("@Hung, @Huy 10h demo sản phẩm nhé"))
