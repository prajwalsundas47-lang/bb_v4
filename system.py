try:
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Context = autoclass("android.content.Context")
    AudioManager = autoclass("android.media.AudioManager")
    CameraManager = autoclass("android.hardware.camera2.CameraManager")
    CameraCharacteristics = autoclass("android.hardware.camera2.CameraCharacteristics")
    Settings = autoclass("android.provider.Settings")
    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
    ANDROID = True
except Exception:
    ANDROID = False


def _audio_manager():
    activity = PythonActivity.mActivity
    return activity.getSystemService(Context.AUDIO_SERVICE)


def volume_up():
    if not ANDROID:
        return "Volume control isn't available on this device."
    try:
        am = _audio_manager()
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
        return "🔊 Volume up."
    except Exception as e:
        return f"Could not change volume: {e}"


def volume_down():
    if not ANDROID:
        return "Volume control isn't available on this device."
    try:
        am = _audio_manager()
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
        return "🔉 Volume down."
    except Exception as e:
        return f"Could not change volume: {e}"


def mute():
    if not ANDROID:
        return "Volume control isn't available on this device."
    try:
        am = _audio_manager()
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, 0)
        return "🔇 Muted."
    except Exception as e:
        return f"Could not mute: {e}"


def _camera_manager():
    activity = PythonActivity.mActivity
    return activity.getSystemService(Context.CAMERA_SERVICE)


def _torch_camera_id(camera_manager):
    for cam_id in camera_manager.getCameraIdList():
        chars = camera_manager.getCameraCharacteristics(cam_id)
        has_flash = chars.get(CameraCharacteristics.FLASH_INFO_AVAILABLE)
        if has_flash:
            return cam_id
    return None


def flashlight_on():
    if not ANDROID:
        return "Flashlight isn't available on this device."
    try:
        cm = _camera_manager()
        cam_id = _torch_camera_id(cm)
        if cam_id is None:
            return "No camera with a flash found."
        cm.setTorchMode(cam_id, True)
        return "🔦 Flashlight on."
    except Exception as e:
        return f"Could not turn on flashlight: {e}"


def flashlight_off():
    if not ANDROID:
        return "Flashlight isn't available on this device."
    try:
        cm = _camera_manager()
        cam_id = _torch_camera_id(cm)
        if cam_id is None:
            return "No camera with a flash found."
        cm.setTorchMode(cam_id, False)
        return "🔦 Flashlight off."
    except Exception as e:
        return f"Could not turn off flashlight: {e}"


def open_wifi_settings():
    if not ANDROID:
        return "Wi-Fi settings aren't available on this device."
    try:
        activity = PythonActivity.mActivity
        intent = Intent(Settings.ACTION_WIFI_SETTINGS)
        activity.startActivity(intent)
        return ("📶 Opening Wi-Fi settings — Android blocks apps from "
                "toggling Wi-Fi directly since Android 10, so tap it yourself.")
    except Exception as e:
        return f"Could not open Wi-Fi settings: {e}"


def set_brightness(level):
    """level: 0-100"""
    if not ANDROID:
        return "Brightness control isn't available on this device."

    try:
        activity = PythonActivity.mActivity

        if not Settings.System.canWrite(activity):
            intent = Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS)
            intent.setData(Uri.parse("package:" + activity.getPackageName()))
            activity.startActivity(intent)
            return ("⚠️ I need permission to change brightness — grant "
                    "'Modify system settings' for BB V4, then try again.")

        value = max(0, min(100, int(level)))
        android_value = int(value * 255 / 100)
        Settings.System.putInt(activity.getContentResolver(), Settings.System.SCREEN_BRIGHTNESS, android_value)
        return f"🔆 Brightness set to {value}%."

    except Exception as e:
        return f"Could not change brightness: {e}"
