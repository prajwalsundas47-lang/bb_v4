from nlp import get_intent
from commands import execute
from ai import think


def process(text):
    intent = get_intent(text)
    reply = execute(intent, text)

    if reply == "Sorry Boss, I didn't understand.":
        return think(text)

    return reply
