import random
import re

SEED_QUESTIONS = [
    "请做一个自我介绍，并简述你最近的项目职责。",
    "说说你如何设计接口测试用例，覆盖哪些场景？",
    "讲讲你做过的自动化测试框架的分层设计。"
]

FOLLOW_RULES = [
    (re.compile(r"\b(jmeter|关联|regex|正则|提取)\b", re.I), "你在 JMeter 做关联时，用的具体正则是什么？举个样例。"),
    (re.compile(r"\b(postman|预请求|环境变量)\b", re.I), "Postman 里预请求脚本与测试脚本分别适合放哪些逻辑？"),
    (re.compile(r"\b(sql|索引|慢查询)\b", re.I), "如何定位并优化一条慢 SQL？你会看哪些指标？"),
    (re.compile(r"\b(selenium|定位|等待)\b", re.I), "Selenium 元素定位失败时，你的重试与显式等待如何设计？"),
    (re.compile(r"\b(性能|吞吐|响应时间|压测)\b", re.I), "压测中你如何选定 RPS 或并发用户数？依据是什么？"),
]

class AIInterviewer:
    def start_chain(self):
        return SEED_QUESTIONS[:]
    
    def follow_up(self, answer: str):
        for pat, q in FOLLOW_RULES:
            if pat.search(answer or ""):
                return q
        if random.random() < 0.2:
            return "能否更量化一点？给出指标、工具与结论。"
        return None
