# storage.py
import os, json, time, collections
from typing import List, Optional
from models import normalize_question

def ensure_app_dirs(base):
	os.makedirs(base, exist_ok=True)
	os.makedirs(os.path.join(base, "audio"), exist_ok=True)

class QuestionStore:
	def __init__(self, base_dir):
		self.base = base_dir
		self.db_path = os.path.join(base_dir, "questions.json")
		self.wrong_path = os.path.join(base_dir, "wrongs.json")
		self.stats_path = os.path.join(base_dir, "stats.json")

	def ensure_seed(self):
		if not os.path.exists(self.db_path):
			seed_src = os.path.join(os.path.dirname(__file__), "data", "seed.json")
			with open(seed_src, "r", encoding="utf-8") as f:
				data = json.load(f)
			self._save_db(data)

	def _load_db(self):
		if not os.path.exists(self.db_path): return []
		with open(self.db_path, "r", encoding="utf-8") as f:
			return json.load(f)

	def _save_db(self, arr):
		with open(self.db_path, "w", encoding="utf-8") as f:
			json.dump(arr, f, ensure_ascii=False, indent=2)

	def add_question(self, q: dict):
		q = normalize_question(q)
		arr = self._load_db()
		arr.append(q)
		self._save_db(arr)

	def query(self, category=None, types=None, difficulties=None) -> List[dict]:
		arr = self._load_db()
		def ok(q):
			return ((not category or q.get("category")==category) and
			        (not types or q.get("type") in types) and
			        (not difficulties or q.get("difficulty") in difficulties))
		return [x for x in arr if ok(x)]

	def count_by_category(self):
		arr = self._load_db()
		c = collections.Counter([x.get("category","未知") for x in arr])
		return dict(c)

	def add_wrong(self, q):
		w = self.load_wrongs()
		w.append(q)
		with open(self.wrong_path, "w", encoding="utf-8") as f:
			json.dump(w[-500:], f, ensure_ascii=False, indent=2)

	def load_wrongs(self):
		if not os.path.exists(self.wrong_path): return []
		with open(self.wrong_path, "r", encoding="utf-8") as f:
			return json.load(f)

	def record_result(self, q, correct: bool, user_ans: str=""):
		stats = self._load_stats()
		cat = q.get("category","未知")
		s = stats.setdefault(cat, {"right":0,"total":0})
		s["total"] += 1
		if correct: s["right"] += 1
		stats["_last"] = {"ts": int(time.time()), "total": sum(v["total"] for k,v in stats.items() if not k.startswith("_")),
		                  "right": sum(v["right"] for k,v in stats.items() if not k.startswith("_"))}
		self._save_stats(stats)

	def _load_stats(self):
		if not os.path.exists(self.stats_path): return {}
		with open(self.stats_path, "r", encoding="utf-8") as f:
			return json.load(f)

	def _save_stats(self, data):
		with open(self.stats_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	def export_interview_report(self, log):
		stats = self._load_stats()
		lines = ["面试记录"]
		for i, item in enumerate(log, 1):
			lines.append(f"Q{i}: {item['q']}")
			lines.append(f"Time: {item['t']}s")
			lines.append("Answer:")
			lines.append(item['a'])
			lines.append("-"*40)
		lines.append("练习正确率（板块）:")
		for k,v in stats.items():
			if k.startswith("_"): continue
			acc = round(100.0*v["right"]/v["total"],1) if v["total"] else 0.0
			lines.append(f"{k}: {acc}%")
		path = os.path.join(self.base, "interview_report.txt")
		with open(path, "w", encoding="utf-8") as f:
			f.write("\n".join(lines))
		return path

class SessionStats:
	def __init__(self, base_dir):
		self.base = base_dir
		self.store = QuestionStore(base_dir)
	def last_summary(self):
		stats = self.store._load_stats()
		total = stats.get("_last",{}).get("total",0)
		right = stats.get("_last",{}).get("right",0)
		acc = round(100.0*right/total,1) if total else 0.0
		return {"total": total, "right": right, "accuracy": acc}
