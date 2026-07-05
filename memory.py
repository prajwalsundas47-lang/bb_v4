import json
import os
from config import MEMORY_FILE

FILE = MEMORY_FILE


def load_memory():
    if not os.path.exists(FILE):
        return {}

    try:
        with open(FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {}


def save_memory(data):
    with open(FILE, "w") as file:
        json.dump(data, file, indent=4)


def remember(key, value):
    data = load_memory()
    data[key.lower()] = value
    save_memory(data)


def recall(key):
    data = load_memory()
    return data.get(key.lower())


def recall_all():
    return load_memory()


def forget(key):
    data = load_memory()

    if key.lower() in data:
        del data[key.lower()]
        save_memory(data)
        return True

    return False
