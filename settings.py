import json
import os
from config import SETTINGS_FILE

DEFAULT_SETTINGS = {
    "voice_enabled": True,
    "wake_word": "bb",
    "theme": "dark",
    "default_city": ""
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(data):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(data, file, indent=4)


def get_setting(key):
    return load_settings().get(key.lower())


def set_setting(key, value):
    data = load_settings()
    data[key.lower()] = value
    save_settings(data)
    return True
