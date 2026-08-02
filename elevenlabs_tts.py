"""
ElevenLabs text-to-speech. Produces much more natural voice output than
Android's built-in TTS engine (used as the fallback in voice.py).

Setup (no code changes needed):
    "set elevenlabs_api_key to YOUR_KEY"   (from inside BB, via chat/voice)

The voice ID defaults to the one you picked (deZSq5evPFppexT3c7TY) and can
be changed the same way:
    "set elevenlabs_voice_id to SOME_OTHER_ID"

If no key is set, or the request fails (no internet, bad key, quota),
speak_elevenlabs() returns a status string and voice.py falls back to
the Android system TTS automatically — BB never goes silent.
"""

import json
import os
import urllib.request
import urllib.error
from settings import get_setting

try:
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    MediaPlayer = autoclass("android.media.MediaPlayer")
    ANDROID = True
except Exception:
    ANDROID = False

API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"

_player = [None]  # kept alive so it isn't garbage-collected mid-playback


def speak_elevenlabs(text):
    """
    Speak text using ElevenLabs. Returns None on success (audio is
    playing), or a short reason string on failure/skip so the caller
    (voice.py) can fall back to Android TTS.
    """
    api_key = get_setting("elevenlabs_api_key")
    if not get_setting("elevenlabs_enabled"):
        return "ElevenLabs disabled."
    if not api_key:
        return "NO_KEY"

    voice_id = get_setting("elevenlabs_voice_id") or "deZSq5evPFppexT3c7TY"

    try:
        payload = json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{API_BASE}/{voice_id}",
            data=payload,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            audio_bytes = response.read()

        return _play_audio(audio_bytes)

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "ElevenLabs key rejected."
        return f"ElevenLabs error (HTTP {e.code})."
    except Exception as e:
        return f"ElevenLabs failed: {e}"


def _play_audio(audio_bytes):
    if not ANDROID:
        return "Playback not available on this device."

    try:
        activity = PythonActivity.mActivity
        cache_dir = activity.getCacheDir().getAbsolutePath()
        path = os.path.join(cache_dir, "bb_speech.mp3")

        with open(path, "wb") as f:
            f.write(audio_bytes)

        old_player = _player[0]
        if old_player is not None:
            try:
                old_player.release()
            except Exception:
                pass

        player = MediaPlayer()
        player.setDataSource(path)
        player.prepare()
        player.start()
        _player[0] = player
        return None

    except Exception as e:
        return f"Could not play audio: {e}"
