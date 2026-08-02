import json
import urllib.request
import urllib.error
from settings import get_setting

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-5-haiku-20241022"

SYSTEM_PROMPT = (
    "You are BB, a witty, concise personal AI assistant running on Prajwal's "
    "phone. Keep replies short (1-3 sentences) and natural to read out loud "
    "over text-to-speech. Avoid markdown formatting."
)


def think(text):
    """
    Fallback responder used whenever BB doesn't recognize an intent
    through the normal rule-based system (nlp.py / commands.py).
    Calls the Claude API for a natural-language reply.

    Falls back to a canned response if no API key is set, and to a
    short error string if the request itself fails (bad key, no
    internet, etc.) so the failure is visible in chat instead of
    silently swallowed.

    Set the key from inside BB itself, no code changes needed:
        "set anthropic_api_key to sk-ant-xxxxx"
    (reuses the existing generic set_setting command)
    """
    api_key = get_setting("anthropic_api_key")

    if not api_key:
        return ("I'm still learning that one, Boss. (No AI key set — say "
                 "\"set anthropic_api_key to YOUR_KEY\" to unlock smarter replies.)")

    try:
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 300,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": text}]
        }).encode("utf-8")

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"].strip()

        return "I'm still learning that one, Boss."

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "⚠️ AI key rejected — double check anthropic_api_key."
        return f"⚠️ AI request failed (HTTP {e.code})."
    except Exception as e:
        return f"⚠️ AI is unreachable right now: {e}"
