def get_intent(text):
    text = text.lower().strip()
    words = text.split()

    # Greetings (whole-word match only, so "think"/"this" don't false-trigger)
    if any(word in ("hi", "hello", "hey") for word in words):
        return "greeting"

    # Identity
    elif "who are you" in text:
        return "who_are_you"

    # Time
    elif "time" in text:
        return "time"

    # Date
    elif "date" in text:
        return "date"

    # Weather
    elif "weather" in text:
        return "weather"

    # Web search
    elif text.startswith("search ") or text.startswith("google ") or text.startswith("look up "):
        return "search"

    # Camera
    elif "take a photo" in text or "take a picture" in text or text == "take photo":
        return "camera"

    # System controls
    elif "volume up" in text or text == "louder":
        return "volume_up"
    elif "volume down" in text or text == "quieter":
        return "volume_down"
    elif "mute" in text:
        return "mute"
    elif "flashlight on" in text or "torch on" in text or "turn on the flashlight" in text or "turn on flashlight" in text:
        return "flashlight_on"
    elif "flashlight off" in text or "torch off" in text or "turn off the flashlight" in text or "turn off flashlight" in text:
        return "flashlight_off"
    elif "wifi" in text:
        return "wifi_settings"
    elif text.startswith("brightness "):
        return "brightness"

    # Settings
    elif text.startswith("set "):
        return "set_setting"
    elif text.startswith("get setting"):
        return "get_setting"

    # Memory
    elif text.startswith("remember"):
        return "remember"

    elif text == "what do you remember":
        return "recall_all"

    elif text.startswith("forget "):
        return "forget"

    elif text.startswith("what is"):
        return "recall"

    elif text.startswith("open "):
        return "open_app"

    # Fun / misc
    elif "joke" in text:
        return "joke"

    elif text in ["exit", "quit", "bye"]:
        return "exit"

    # Calculator
    allowed = "0123456789+-*/().%x "

    if text and all(ch in allowed for ch in text):
        return "calculate"

    return "unknown"
