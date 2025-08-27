# models.py
def normalize_question(q: dict) -> dict:
	q = {**q}
	q["type"] = q.get("type","qa")
	q["category"] = q.get("category","测试理论")
	q["difficulty"] = q.get("difficulty","初")
	q["question"] = q.get("question","").strip()
	q["options"] = q.get("options", [])
	q["answer"] = q.get("answer","").strip()
	q["tags"] = q.get("tags", [])
	return q
