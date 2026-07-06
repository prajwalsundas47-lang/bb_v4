try:
    import urllib.request
    import urllib.parse
    import json
    HAS_NET = True
except ImportError:
    HAS_NET = False


def search_web(query):
    """
    Quick web search using DuckDuckGo's free Instant Answer API.
    No API key required. Returns a short text answer when available,
    otherwise a link to full search results.
    """
    query = query.strip()

    if not query:
        return "What do you want me to search for?"

    if not HAS_NET:
        return "Search is not available on this device."

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        with urllib.request.urlopen(url, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))

        abstract = data.get("AbstractText")
        if abstract:
            return f"🔎 {abstract}"

        related = data.get("RelatedTopics", [])
        for item in related:
            text = item.get("Text")
            if text:
                return f"🔎 {text}"

        return f"🔎 No quick answer found. Full results: https://duckduckgo.com/?q={encoded}"

    except Exception as e:
        return f"Search failed: {e}"
