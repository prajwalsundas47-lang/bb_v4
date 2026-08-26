"""
service.py - Screen recording foreground service for BB V4.

Started via startForegroundService()/startService() from
screen_recorder_control.py. Reads the MediaProjection permission result
and recording settings from Intent extras, then captures the screen to
an MP4 using MediaProjection + VirtualDisplay + MediaRecorder.

Stopped when the main app calls stopService() directly - cleanup runs
in the atexit handler below.
"""
import os
import time
import atexit
import traceback
from datetime import datetime

from jnius import autoclass, cast

PythonService = autoclass('org.kivy.android.PythonService')
Context = autoclass('android.content.Context')
MediaRecorder = autoclass('android.media.MediaRecorder')
DisplayMetrics = autoclass('android.util.DisplayMetrics')
Environment = autoclass('android.os.Environment')

service = PythonService.mService
service.setAutoRestartService(False)

intent = service.getIntent()
result_code = intent.getIntExtra("projection_result_code", 0)
projection_data = intent.getParcelableExtra("projection_result_data")
width = intent.getIntExtra("width", 720)
height = intent.getIntExtra("height", 1280)
fps = intent.getIntExtra("fps", 30)
bitrate = intent.getIntExtra("bitrate", 5_000_000)
audio_mode = intent.getStringExtra("audio_mode") or "none"

_media_recorder = [None]
_virtual_display = [None]
_media_projection = [None]


def _output_path():
    movies_dir = Environment.getExternalStoragePublicDirectory(
        Environment.DIRECTORY_MOVIES
    ).getAbsolutePath()
    folder = os.path.join(movies_dir, "BBV4")
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"BB_recording_{stamp}.mp4")


def _start_foreground():
    import notification_helper as notif
    notification = notif.build_recording_notification(service)
    service.startForeground(4201, notification)


def _start_recording():
    output_path = _output_path()

    recorder = MediaRecorder()
    if audio_mode == "mic":
        recorder.setAudioSource(MediaRecorder.AudioSource.MIC)
    recorder.setVideoSource(MediaRecorder.VideoSource.SURFACE)
    recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
    if audio_mode == "mic":
        recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
    recorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264)
    recorder.setVideoSize(width, height)
    recorder.setVideoFrameRate(fps)
    recorder.setVideoEncodingBitRate(bitrate)
    recorder.setOutputFile(output_path)
    recorder.prepare()

    surface = recorder.getSurface()

    manager = cast(
        'android.media.projection.MediaProjectionManager',
        service.getSystemService(Context.MEDIA_PROJECTION_SERVICE),
    )
    projection = manager.getMediaProjection(result_code, projection_data)
    density = service.getResources().getDisplayMetrics().densityDpi

    virtual_display = projection.createVirtualDisplay(
        "BBV4ScreenCapture", width, height, density,
        16, surface, None, None,
    )

    recorder.start()
    _media_recorder[0] = recorder
    _virtual_display[0] = virtual_display
    _media_projection[0] = projection


def _cleanup(*_args):
    try:
        if _media_recorder[0]:
            try:
                _media_recorder[0].stop()
            except Exception:
                pass
            _media_recorder[0].release()
    except Exception:
        traceback.print_exc()
    try:
        if _virtual_display[0]:
            _virtual_display[0].release()
    except Exception:
        traceback.print_exc()
    try:
        if _media_projection[0]:
            _media_projection[0].stop()
    except Exception:
        traceback.print_exc()


atexit.register(_cleanup)

try:
    _start_foreground()
    _start_recording()
except Exception:
    traceback.print_exc()
    _cleanup()
    raise

while True:
    time.sleep(1)
