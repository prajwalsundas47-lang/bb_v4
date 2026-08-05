try:
    import sympy
    from sympy import symbols, diff, integrate, limit, solve, simplify, sympify, oo
    from sympy.parsing.sympy_parser import parse_expr
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

x, y, z = symbols("x y z") if HAS_SYMPY else (None, None, None)


def solve_math(text):
    """
    Handles calculus/algebra phrased naturally:
      "derivative of x^2 + 3x"
      "integral of sin(x)"
      "integrate x^2 from 0 to 1"
      "limit of 1/x as x approaches 0"
      "solve x^2 - 4 = 0"
    """
    if not HAS_SYMPY:
        return "Advanced math needs the sympy library — not installed on this build."

    text = text.lower().strip()

    try:
        if text.startswith("derivative of") or text.startswith("differentiate"):
            expr_str = text.split("of", 1)[-1].strip() if "of" in text else text.replace("differentiate", "").strip()
            expr = parse_expr(expr_str.replace("^", "**"))
            result = diff(expr, x)
            return f"📐 d/dx [{expr_str}] = {simplify(result)}"

        if text.startswith("integral of") or text.startswith("integrate"):
            body = text.split("of", 1)[-1].strip() if "of" in text else text.replace("integrate", "").strip()
            if "from" in body and "to" in body:
                expr_part, bounds = body.split("from", 1)
                lower, upper = bounds.split("to")
                expr = parse_expr(expr_part.strip().replace("^", "**"))
                result = integrate(expr, (x, sympify(lower.strip()), sympify(upper.strip())))
                return f"📐 ∫ {expr_part.strip()} dx from {lower.strip()} to {upper.strip()} = {result}"
            expr = parse_expr(body.replace("^", "**"))
            result = integrate(expr, x)
            return f"📐 ∫ {body} dx = {result} + C"

        if text.startswith("limit of"):
            body = text.replace("limit of", "").strip()
            expr_part, point_part = body.split("as x approaches")
            expr = parse_expr(expr_part.strip().replace("^", "**"))
            point = oo if "infinity" in point_part else sympify(point_part.strip())
            result = limit(expr, x, point)
            return f"📐 lim(x→{point_part.strip()}) {expr_part.strip()} = {result}"

        if text.startswith("solve"):
            body = text.replace("solve", "").strip()
            if "=" in body:
                left, right = body.split("=")
                eq = parse_expr(left.strip().replace("^", "**")) - parse_expr(right.strip().replace("^", "**"))
            else:
                eq = parse_expr(body.replace("^", "**"))
            result = solve(eq, x)
            return f"📐 Solution: x = {result}"

        return "Try: 'derivative of x^2', 'integral of sin(x)', 'limit of 1/x as x approaches 0', or 'solve x^2 - 4 = 0'."

    except Exception as e:
        return f"Couldn't parse that expression: {e}"
