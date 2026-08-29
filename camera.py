try:    
    from jnius import autoclass, cast
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    MediaStore = autoclass("android.provider.MediaStore")
    ANDROID = True
except Exception:
    ANDROID = False

def ensure_camera_permission():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Manifest = autoclass('android.Manifest$permission')
    ContextCompat = autoclass('androidx.core.content.ContextCompat')
    ActivityCompat = autoclass('androidx.core.app.ActivityCompat')

    activity = PythonActivity.mActivity
    perm = Manifest.CAMERA
    if ContextCompat.checkSelfPermission(activity, perm) != 0:  # 0 = PERMISSION_GRANTED
        ActivityCompat.requestPermissions(activity, [perm], 101)
        return False
    return True
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
 
