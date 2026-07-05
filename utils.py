def clean_text(text):
    """Lowercase and strip whitespace from input text."""
    return text.strip().lower()


def safe_get(d, key, default=None):
    """Safely get a value from a dict-like object."""
    if isinstance(d, dict):
        return d.get(key, default)
    return default
