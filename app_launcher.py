from apps import APPS
import difflib

try:
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    activity = PythonActivity.mActivity

except Exception:
    activity = None


def open_app(app_name):

    app_name = app_name.lower().strip()

    if app_name not in APPS:
        close_matches = difflib.get_close_matches(app_name, APPS.keys(), n=1, cutoff=0.6)

        if close_matches:
            match = close_matches[0]
            app_name = match
        else:
            return f"I don't know the app '{app_name}'."

    if activity is None:
        return "Android launcher is not available."

    package = APPS[app_name]

    try:
        pm = activity.getPackageManager()

        intent = pm.getLaunchIntentForPackage(package)

        if intent is None:
            return f"{app_name.title()} is not installed."

        activity.startActivity(intent)

        return f"📱 Opening {app_name.title()}..."

    except Exception as e:
        return str(e)
