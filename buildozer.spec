[app]
title = QATrainer
package.name = qatrainer
package.domain = org.example
version = 0.1.0

source.dir = .
source.include_exts = py,kv,json,txt,xlsx
entrypoint = main.py
requirements = python3,kivy==2.2.1,openpyxl,pyjnius

orientation = portrait

[android]
android.api = 35
android.minapi = 21
android.permissions = RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
