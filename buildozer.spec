[app]
title = BB V4
package.name = bbv4
package.domain = org.bb

source.dir = .
source.include_exts = py,png,jpg,json,xml

version = 4.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,pyjnius,certifi,sympy,android
services = RecordingService:service.py
orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO,INTERNET,MODIFY_AUDIO_SETTINGS,CAMERA,WRITE_SETTINGS,QUERY_ALL_PACKAGES,FOREGROUND_SERVICE,FOREGROUND_SERVICE_MEDIA_PROJECTION,POST_NOTIFICATIONS,SYSTEM_ALERT_WINDOW,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,BIND_ACCESSIBILITY_SERVICE
android.api = 33
android.minapi = 29
android.archs = arm64-v8a

android.accept_sdk_license = True
android.add_resources = src/res:
android.add_src = src
android.manifest_template = src/templates/AndroidManifest.tmpl.xml

[buildozer]
log_level = 3
warn_on_root = 1
