"""
Wraps the screen recorder's Activity-side logic (from the standalone
project's main.py) as plain functions BB's main.py/commands.py can call,
instead of a separate Kivy App class.
"""
from jnius import autoclass
from recording_settings import RecordingSettings
import notification_helper as notif

PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
Context = autoclass('android.content.Context')
VERSION = autoclass('android.os.Build$VERSION')

MEDIA_PROJECTION_REQUEST_CODE = 4200
_pending_settings = [None]
_is_recording = [False]

# Buildozer generates a dedicated service class for named services
# (services = RecordingService:service.py:foreground) instead of using
# the generic org.kivy.android.PythonService.
SERVICE_CLASS_NAME = "org.bb.bbv4.ServiceRecordingservice"


def start_recording(on_error=None, on_success=None):
    """Triggers the one-time system consent dialog, then starts the
    foreground recording service once granted."""
    from android import activity as android_activity

    _pending_settings[0] = RecordingSettings()  # sensible defaults
    android_activity.bind(
        on_activity_result=lambda *a: _on_activity_result(*a, on_error=on_error, on_success=on_success)
    )

    try:
        activity = PythonActivity.mActivity
        MediaProjectionManager = autoclass('android.media.projection.MediaProjectionManager')
        manager = activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
        capture_intent = manager.createScreenCaptureIntent()
        activity.startActivityForResult(capture_intent, MEDIA_PROJECTION_REQUEST_CODE)
    except Exception as e:
        if on_error:
            on_error(f"Couldn't open the recording permission dialog: {e}")


def _on_activity_result(request_code, result_code, data, on_error=None, on_success=None):
    if request_code != MEDIA_PROJECTION_REQUEST_CODE:
        return
    RESULT_OK = -1
    if result_code != RESULT_OK or data is None:
        if on_error:
            on_error("Screen recording permission was denied.")
        return
    try:
        _start_service(result_code, data, _pending_settings[0])
        if on_success:
            on_success("Recording started.")
    except Exception as e:
        if on_error:
            on_error(f"Couldn't start recording service: {e}")


def _start_service(result_code, projection_data, settings):
    activity = PythonActivity.mActivity
    ServiceClass = autoclass(SERVICE_CLASS_NAME)
    service_intent = Intent(activity, ServiceClass)
    service_intent.putExtra("projection_result_code", result_code)
    service_intent.putExtra("projection_result_data", projection_data)
    service_intent.putExtra("width", settings.width)
    service_intent.putExtra("height", settings.height)
    service_intent.putExtra("fps", settings.fps)
    service_intent.putExtra("bitrate", settings.bitrate)
    service_intent.putExtra("mime", settings.mime)
    service_intent.putExtra("audio_mode", settings.audio_mode)

    if VERSION.SDK_INT >= 26:
        activity.startForegroundService(service_intent)
    else:
        activity.startService(service_intent)
    _is_recording[0] = True


def stop_recording():
    activity = PythonActivity.mActivity
    stop_intent = Intent(notif.ACTION_STOP)
    stop_intent.setPackage(activity.getPackageName())
    activity.sendBroadcast(stop_intent)
    _is_recording[0] = False


def is_recording():
    return _is_recording[0]
