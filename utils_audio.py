import os, time
try:
from jnius import autoclass
except Exception:
autoclass = None

class AudioRecorder:
def __init__(self, base_dir):
self.base = base_dir
self._rec = None
self.path = None
def start(self):
if not autoclass:
raise RuntimeError("pyjnius/MediaRecorder 不可用")
MediaRecorder = autoclass('android.media.MediaRecorder')
AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
self._rec = MediaRecorder()
self._rec.setAudioSource(AudioSource.MIC)
self._rec.setOutputFormat(OutputFormat.MPEG_4)
self._rec.setAudioEncoder(AudioEncoder.AAC)
self.path = os.path.join(self.base, "audio", f"ans_{int(time.time())}.m4a")
self._rec.setOutputFile(self.path)
self._rec.prepare()
self._rec.start()
def stop(self):
if not self._rec:
return ""
self._rec.stop()
self._rec.release()
self._rec = None
return self.path
def is_recording(self):
return self._rec is not None
