import json
import urllib.request
import urllib.error
from settings import get_setting

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are BB, a witty, concise personal AI assistant running on Prajwal's "
    "phone. Keep replies short (1-3 sentences) and natural to read out loud "
    "over text-to-speech. Avoid markdown formatting. You have a web_search "
    "tool available — use it whenever the answer depends on current, "
    "changing, or recent information (news, prices, scores, who currently "
    "holds a role, what's the latest version of something, etc). Don't "
    "narrate that you searched, just answer naturally."
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
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": text}],
            "tools": [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 3
            }]
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

        # Web search adds server-side round trips, so give it more time
        # than a plain text-only reply needs.
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))

        # When web_search is used, content mixes tool-use/tool-result
        # blocks in with one or more "text" blocks — only the text
        # blocks are the actual reply, so join all of them in order.
        reply_parts = [
            block["text"] for block in data.get("content", [])
            if block.get("type") == "text" and block.get("text")
        ]
        if reply_parts:
            return " ".join(reply_parts).strip()

        return "I'm still learning that one, Boss."

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "⚠️ AI key rejected — double check anthropic_api_key."
        return f"⚠️ AI request failed (HTTP {e.code})."
    except Exception as e:
        return f"⚠️ AI is unreachable right now: {e}"
