def calculate(text):
    """Safely evaluate a basic math expression typed by the user."""
    try:
        expression = text.replace("x", "*").replace("X", "*")
        allowed = "0123456789+-*/().% "

        if not expression or not all(ch in allowed for ch in expression):
            return "Invalid calculation."

        answer = eval(expression)
        return str(answer)

    except Exception:
        return "Invalid calculation."
