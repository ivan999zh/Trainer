import os, json, random, time
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty, DictProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from storage import QuestionStore, SessionStats, ensure_app_dirs
from importer import import_from_excel
from ai_interviewer import AIInterviewer
from utils_audio import AudioRecorder

CATEGORIES = [
"测试理论","工具-Postman","工具-Jmeter","工具-Selenium",
"自动化框架","性能安全","编程-Python","编程-SQL"
]
DIFFICULTIES = ["初","中","高"]

class HomeScreen(Screen):
pass

class ManageScreen(Screen):
status = StringProperty("")
def on_pre_enter(self, *args):
self.refresh_counts()
def refresh_counts(self):
store = QuestionStore(App.get_running_app().user_data_dir)
counts = store.count_by_category()
lines = [f"{k}: {v}" for k,v in sorted(counts.items())]
self.ids.counts.text = "\n".join(lines) if lines else "暂无题目"
def import_excel(self, path):
try:
store = QuestionStore(App.get_running_app().user_data_dir)
n = import_from_excel(path, store)
self.status = f"导入成功：{n} 条"
self.refresh_counts()
except Exception as e:
self.status = f"导入失败：{e}"
def add_manual(self):
store = QuestionStore(App.get_running_app().user_data_dir)
data = {
"type": self.ids.type_spinner.text,
"category": self.ids.cat_spinner.text,
"difficulty": self.ids.diff_spinner.text,
"question": self.ids.q_input.text.strip(),
"options": [o.strip() for o in self.ids.opt_input.text.split("\n") if o.strip()] if self.ids.type_spinner.text=="mcq" else [],
"answer": self.ids.ans_input.text.strip(),
"tags": [t.strip() for t in self.ids.tag_input.text.split(",") if t.strip()]
}
store.add_question(data)
self.status = "已添加"
self.clear_form()
self.refresh_counts()
def clear_form(self):
self.ids.q_input.text = ""
self.ids.opt_input.text = ""
self.ids.ans_input.text = ""
self.ids.tag_input.text = ""

class PracticeScreen(Screen):
questions = ListProperty([])
index = NumericProperty(0)
timer = NumericProperty(0)
limit_seconds = NumericProperty(0)
mode_random = BooleanProperty(False)
show_result = BooleanProperty(False)
result_text = StringProperty("")
progress = StringProperty("")
session_cfg = DictProperty({})
shuffled_map = DictProperty({})
selected_idx = NumericProperty(-1)

def setup_session(self, cfg):
self.session_cfg = cfg
store = QuestionStore(App.get_running_app().user_data_dir)
q = store.query(category=cfg.get("category"), types=cfg.get("types"), difficulties=cfg.get("difficulties"))
if cfg.get("random"):
random.shuffle(q)
count = cfg.get("count") or len(q)
self.questions = q[:count]
self.limit_seconds = cfg.get("time_limit", 0)
self.index = 0
self.timer = 0
self.show_result = False
self.result_text = ""
self.selected_idx = -1
self.shuffled_map = {}
self.update_view()
if self.limit_seconds > 0:
Clock.unschedule(self._tick)
Clock.schedule_interval(self._tick, 1)

def _tick(self, dt):
self.timer += 1
remain = max(0, self.limit_seconds - self.timer)
self.ids.time_label.text = f"剩余：{remain}s" if self.limit_seconds>0 else ""
if self.limit_seconds>0 and remain<=0:
self.finish_session()
return False

def current(self):
return self.questions[self.index] if 0 <= self.index < len(self.questions) else None

def update_view(self):
q = self.current()
if not q:
self.finish_session()
return
self.progress = f"{self.index+1}/{len(self.questions)}"
self.ids.q_text.text = q["question"]
self.ids.type_label.text = f'{q["type"].upper()} | {q["category"]} | {q["difficulty"]}'
self.ids.answer_input.text = ""
self.selected_idx = -1
self.show_result = False
self.result_text = ""
self.ids.options_box.clear_widgets()
if q["type"]=="mcq":
from kivy.uix.togglebutton import ToggleButton
opts = q.get("options", [])[:]
random_order = list(range(len(opts)))
random.shuffle(random_order)
self.shuffled_map[str(self.index)] = random_order
for i, orig_i in enumerate(random_order):
btn = ToggleButton(text=opts[orig_i], group='opts', size_hint_y=None, height='44dp')
def on_pick(b, idx=i):
self.selected_idx = idx
btn.bind(on_press=on_pick)
self.ids.options_box.add_widget(btn)
else:
self.ids.options_box.add_widget(self.ids.answer_input)

def submit(self):
q = self.current()
if not q: return
store = QuestionStore(App.get_running_app().user_data_dir)
correct = False
user_ans = ""
if q["type"]=="mcq":
if self.selected_idx<0:
return
perm = self.shuffled_map.get(str(self.index), [])
orig_idx = perm[self.selected_idx] if self.selected_idx<len(perm) else -1
user_ans = str(orig_idx)
correct = (str(q.get("answer","")) == user_ans)
else:
user_ans = self.ids.answer_input.text.strip()
key = q.get("answer","").strip().lower()
correct = (key!="" and key in user_ans.lower())
if correct:
self.result_text = "✅ 正确"
store.record_result(q, True)
else:
self.result_text = f'❌ 错误。参考：{q.get("answer","")[:120]}'
store.record_result(q, False, user_ans)
store.add_wrong(q)
self.show_result = True

def next_q(self):
if self.index+1 >= len(self.questions):
self.finish_session()
return
self.index += 1
self.update_view()

def redo_wrongs(self):
store = QuestionStore(App.get_running_app().user_data_dir)
self.questions = store.load_wrongs()
random.shuffle(self.questions)
self.index = 0
self.limit_seconds = 0
self.timer = 0
self.update_view()

def finish_session(self):
Clock.unschedule(self._tick)
self.ids.q_text.text = "本次练习完成"
summary = SessionStats(App.get_running_app().user_data_dir).last_summary()
self.result_text = f'正确率：{summary.get("accuracy",0)}%  |  总题数：{summary.get("total",0)}'
self.show_result = True

class InterviewScreen(Screen):
index = NumericProperty(0)
timer = NumericProperty(0)
running = BooleanProperty(False)
log = ListProperty([])
rec_status = StringProperty("")
def on_pre_enter(self, *args):
self.ai = AIInterviewer()
self.rec = AudioRecorder(App.get_running_app().user_data_dir)
self.reset_chain()

def reset_chain(self):
self.index = 0
self.timer = 0
self.running = False
self.log = []
self.questions = self.ai.start_chain()
self.update_view()

def update_view(self):
q = self.questions[self.index] if self.index < len(self.questions) else None
self.ids.iq_text.text = q or "面试结束"
self.ids.answer_input.text = ""
self.timer = 0
self.running = False
Clock.unschedule(self._tick)

def start_pause(self):
self.running = not self.running
if self.running:
Clock.schedule_interval(self._tick, 1)

def _tick(self, dt):
if not self.running: return False
self.timer += 1

def record_toggle(self):
try:
if not self.rec.is_recording():
self.rec.start()
self.rec_status = "录音中..."
else:
path = self.rec.stop()
self.rec_status = f"已保存：{os.path.basename(path)}"
except Exception as e:
self.rec_status = f"录音不可用：{e}"

def next_q(self):
q = self.questions[self.index] if self.index < len(self.questions) else None
ans = self.ids.answer_input.text.strip()
self.log.append({"q": q, "a": ans, "t": self.timer})
follow = self.ai.follow_up(ans)
if follow:
self.questions.insert(self.index+1, follow)
self.index += 1
if self.index >= len(self.questions):
self.ids.iq_text.text = "面试结束，已生成报告。"
self.running = False
self._export_report()
return
self.update_view()

def _export_report(self):
store = QuestionStore(App.get_running_app().user_data_dir)
report_path = store.export_interview_report(self.log)
self.ids.report_label.text = f"报告：{report_path}"

class Root(ScreenManager):
pass

class QATrainerApp(App):
def build(self):
ensure_app_dirs(self.user_data_dir)
store = QuestionStore(self.user_data_dir)
store.ensure_seed()
return Builder.load_file('app.kv')

if __name__ == "__main__":
QATrainerApp().run()
