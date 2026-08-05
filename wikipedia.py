try:
    import urllib.request
    import urllib.parse
    import json
    import ssl
    import certifi
    HAS_NET = True
except ImportError:
    HAS_NET = False


def search_wikipedia(query):
    """
    Free Wikipedia REST API — no key needed. Returns a brief summary
    of the top matching article.
    """
    query = query.strip()

    if not query:
        return "What do you want me to look up on Wikipedia?"

    if not HAS_NET:
        return "Wikipedia lookup isn't available on this device."

    try:
        encoded = urllib.parse.quote(query.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers={"User-Agent": "BB-V4/1.0"})

        with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
            data = json.loads(response.read().decode("utf-8"))

        extract = data.get("extract")
        if extract:
            return f"📖 {extract}"

        return f"I couldn't find a clear Wikipedia article for '{query}'."

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"No Wikipedia article found for '{query}'."
        return f"Wikipedia lookup failed (HTTP {e.code})."
    except Exception as e:
        return f"Wikipedia lookup failed: {e}"
