[app]
title = BB V4
package.name = bbv4
package.domain = org.bb

source.dir = .
source.include_exts = py,png,jpg,json,xml

version = 4.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,pyjnius,certifi,sympy,android
services = ServiceRecordingService:src/org/bb/bbv4/ServiceRecordingService.java
orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO,FOREGROUND_SERVICE,SYSTEM_ALERT_WINDOW,...(your existing ones)
android.api = 33
android.minapi = 29
android.archs = arm64-v8a

android.accept_sdk_license = True
android.add_resources = src/templates
android.add_src = src
p4a.hook = p4a_hook.py

[buildozer]
log_level = 3
warn_on_root = 1
