try:
    import urllib.request
except ImportError:
    urllib = None


def get_weather(city=""):
    """
    Fetches a short weather summary using wttr.in (no API key required).
    Pass an empty string to auto-detect location by IP.
    """
    if urllib is None:
        return "Weather module is not available."

    try:
        location = city.strip() if city else ""
        url = f"https://wttr.in/{location}?format=3"

        with urllib.request.urlopen(url, timeout=6) as response:
            data = response.read().decode("utf-8").strip()
            return f"🌦️ {data}"

    except Exception as e:
        return f"Could not fetch weather: {e}"
