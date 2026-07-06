try:
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    MediaStore = autoclass("android.provider.MediaStore")
    ANDROID = True
except Exception:
    ANDROID = False


def open_camera():
    """
    Launches the phone's camera app directly in photo-capture mode.
    (Full in-app silent capture would need the Camera2/CameraX API,
    which is a much bigger project — this gets you snapping fast.)
    """
    if not ANDROID:
        return "Camera is not available on this device."

    try:
        activity = PythonActivity.mActivity
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        activity.startActivity(intent)
        return "📷 Opening camera..."
    except Exception as e:
        return f"Could not open camera: {e}"
