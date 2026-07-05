def get_intent(text):
    text = text.lower().strip()

    # Greetings
    if any(word in text for word in ["hi", "hello", "hey"]):
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
