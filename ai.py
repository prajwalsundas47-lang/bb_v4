import json
import urllib.request
import urllib.error
from settings import get_setting

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = (
    "You are BB, a witty, concise personal AI assistant running on Prajwal's "
    "phone. For any question with real complexity (advice, comparisons, "
    "multi-step reasoning), think it through step by step *silently* first, "
    "then give ONLY the polished final answer — 1-3 sentences, natural to "
    "read out loud over text-to-speech, no markdown, no visible reasoning. "
    "You have a web_search tool available — use it whenever the answer "
    "depends on current, changing, or recent information. Don't narrate "
    "that you searched or that you reasoned, just answer naturally."
)

# Rolling conversation history, kept in memory for the app session.
# Each entry is {"role": "user"|"assistant", "content": "..."}.
HISTORY = []
MAX_TURNS = 6  # 6 messages = 3 user/assistant exchanges of context


def clear_history():
    """Wipe conversation memory — used by the 'new conversation' command."""
    HISTORY.clear()


def think(text):
    """
    Fallback responder used whenever BB doesn't recognize an intent
    through the normal rule-based system (nlp.py / commands.py).
    Calls the Claude API for a natural-language reply, including the
    last few exchanges so follow-ups like "what about tomorrow" resolve
    correctly.

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

    messages = HISTORY + [{"role": "user", "content": text}]

    try:
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": messages,
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

        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))

        reply_parts = [
            block["text"] for block in data.get("content", [])
            if block.get("type") == "text" and block.get("text")
        ]
        reply = " ".join(reply_parts).strip() if reply_parts else "I'm still learning that one, Boss."

        # Only commit to history on a real reply — not on canned fallbacks.
        if reply_parts:
            HISTORY.append({"role": "user", "content": text})
            HISTORY.append({"role": "assistant", "content": reply})
            del HISTORY[:-MAX_TURNS]  # keep only the most recent MAX_TURNS messages

        return reply

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "⚠️ AI key rejected — double check anthropic_api_key."
        return f"⚠️ AI request failed (HTTP {e.code})."
    except Exception as e:
        return f"⚠️ AI is unreachable right now: {e}"
