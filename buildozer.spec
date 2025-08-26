[app]
title = QATrainer
package.name = qatrainer
package.domain = org.example
source.dir = .
source.include_exts = py,kv,json,txt,xlsx
requirements = python3,kivy,openpyxl,pyjnius
orientation = portrait
entrypoint = main.py

[android]
android.api = 33
android.minapi = 21
android.permissions = RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
