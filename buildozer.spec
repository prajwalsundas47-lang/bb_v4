[app]
title = BB V4
package.name = bbv4
package.domain = org.bb

source.dir = .
source.include_exts = py,png,jpg,json

version = 4.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO,INTERNET,MODIFY_AUDIO_SETTINGS,CAMERA,WRITE_SETTINGS

android.api = 29
android.minapi = 21
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
