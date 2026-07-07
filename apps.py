# Each app name maps to a LIST of candidate package names, since
# Samsung (and other manufacturers) ship their own versions of common
# apps with different package names than stock Android/Google.
# app_launcher tries each candidate in order until one is installed.

APPS = {
    "youtube": ["com.google.android.youtube"],
    "chrome": ["com.android.chrome"],
    "camera": ["com.sec.android.app.camera", "com.android.camera"],
    "calculator": ["com.sec.android.app.popupcalculator", "com.google.android.calculator"],
    "settings": ["com.android.settings"],
    "phone": ["com.samsung.android.dialer", "com.android.dialer", "com.google.android.dialer"],
    "contacts": ["com.samsung.android.app.contacts", "com.android.contacts", "com.google.android.contacts"],
    "messages": ["com.samsung.android.messaging", "com.google.android.apps.messaging"],
    "whatsapp": ["com.whatsapp"],
    "play store": ["com.android.vending"],
    "gmail": ["com.google.android.gm"],
    "maps": ["com.google.android.apps.maps"],
    "instagram": ["com.instagram.android"],
    "messenger": ["com.facebook.orca"],
    "gallery": ["com.sec.android.gallery3d", "com.samsung.android.gallery"],
    "clock": ["com.sec.android.app.clockpackage", "com.google.android.deskclock"],
    "spotify": ["com.spotify.music"],
    "telegram": ["org.telegram.messenger"],
    "discord": ["com.discord"],
}
