import datetime
from memory import remember, recall, recall_all, forget
from app_launcher import open_app
from calculator import calculate
from weather import get_weather
from settings import get_setting, set_setting
from search import search_web
from camera import open_camera
from system import volume_up, volume_down, mute, flashlight_on, flashlight_off, open_wifi_settings, set_brightness


def execute(intent, text):

    if intent == "greeting":
        return "Hello Boss! 👋"

    elif intent == "who_are_you":
        return "I am BB V4, your personal AI assistant."

    elif intent == "time":
        return datetime.datetime.now().strftime("%I:%M %p")

    elif intent == "date":
        return datetime.datetime.now().strftime("%d %B %Y")

    elif intent == "weather":
        city = text.replace("weather", "", 1).strip()
        return get_weather(city)

    elif intent == "search":
        query = text
        for prefix in ("search ", "google ", "look up "):
            if query.startswith(prefix):
                query = query[len(prefix):]
                break
        return search_web(query.strip())

    elif intent == "camera":
        return open_camera()

    elif intent == "volume_up":
        return volume_up()

    elif intent == "volume_down":
        return volume_down()

    elif intent == "mute":
        return mute()

    elif intent == "flashlight_on":
        return flashlight_on()

    elif intent == "flashlight_off":
        return flashlight_off()

    elif intent == "wifi_settings":
        return open_wifi_settings()

    elif intent == "brightness":
        level_str = text.replace("brightness", "", 1).strip().rstrip("%")
        try:
            return set_brightness(int(level_str))
        except ValueError:
            return "Example: brightness 70"

    elif intent == "set_setting":
        # Example: set theme to light
        body = text.replace("set", "", 1).strip()

        if " to " in body:
            key, value = body.split(" to ", 1)
            set_setting(key.strip(), value.strip())
            return f"🛠️ Setting '{key.strip()}' updated to '{value.strip()}'."

        return "Example: set theme to dark"

    elif intent == "get_setting":
        key = text.replace("get setting", "", 1).strip()
        value = get_setting(key)

        if value is not None:
            return f"{key} = {value}"

        return "I don't have that setting."

    elif intent == "remember":
        sentence = text.replace("remember", "", 1).strip()

        if " is " in sentence:
            key, value = sentence.split(" is ", 1)
            remember(key.strip(), value.strip())
            return "🧠 I'll remember that."

        return "Example: remember my name is Prajwal"

    elif intent == "recall":
        key = text.replace("what is", "", 1).strip()

        value = recall(key)

        if value:
            return f"{key.title()} is {value}."

        return "I don't remember that."

    elif intent == "recall_all":
        data = recall_all()

        if not data:
            return "I don't remember anything yet."

        reply = "🧠 I remember:\n"

        for key, value in data.items():
            reply += f"\n• {key} = {value}"

        return reply

    elif intent == "forget":
        key = text.replace("forget", "", 1).strip()

        if forget(key):
            return f"🗑️ Forgot '{key}'."

        return "I didn't have that remembered."

    elif intent == "calculate":
        return calculate(text)

    elif intent == "open_app":
        app = text.replace("open", "", 1).strip()
        return open_app(app)

    elif intent == "joke":
        return "Why do programmers prefer dark mode? Because light attracts bugs. 😄"

    elif intent == "exit":
        return "Goodbye Boss! 👋"

    return "Sorry Boss, I didn't understand."
