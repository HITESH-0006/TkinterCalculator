"""Tkinter Calculator
-------------------
A GUI calculator using Tkinter's Window (Tk), Entry and Button widgets.
Supports + - * / with a display field, digit buttons, equals and clear.
Runs as-is in IDLE (F5) - uses only the Python standard library.
"""

import ast
import math
import operator
import re
import tkinter as tk
from functools import partial

# ---------- Constants ----------
DIGITS = set("0123456789")
OPERATORS = "+-*/"
MAX_LENGTH = 30

DISPLAY_FONT = ("Segoe UI", 18)
BUTTON_FONT = ("Segoe UI", 12)

# Button layout (matches the expected output screenshot)
KEYPAD = (
    ("1", "2", "3"),
    ("4", "5", "6"),
    ("7", "8", "9"),
    ("0", "+", "-"),
    ("*", "/", "="),
)

BINARY_OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


# ---------- Calculation helpers ----------
def evaluate(node):
    """Safely evaluate a parsed arithmetic expression (no eval())."""
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATIONS:
        return BINARY_OPERATIONS[type(node.op)](evaluate(node.left), evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    raise ValueError("Unsupported expression")


def safe_eval(expression):
    """Evaluate a string such as '2+3*4' and return the numeric result."""
    return evaluate(ast.parse(expression, mode="eval"))


def format_result(value):
    """Turn a number into a clean string (5.0 -> '5', 0.1+0.2 -> '0.3')."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Result out of range")
        value = round(value, 10)
        if value.is_integer():
            return str(int(value))
        return f"{value:.10f}".rstrip("0")
    return str(value)


# ---------- Calculator application ----------
class Calculator:
    def __init__(self, root):
        self.root = root
        self.expression = ""      # what the user has typed so far
        self.fresh = False        # True right after '=' or an error message

        root.title("Calculator")
        root.resizable(False, False)

        self.display_var = tk.StringVar()
        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.pack()

        self._build_display()
        self._build_buttons()

        root.bind("<Key>", self.on_key)
        root.focus_set()

    # ----- UI construction -----
    def _build_display(self):
        self.display = tk.Entry(
            self.frame,
            textvariable=self.display_var,
            font=DISPLAY_FONT,
            justify="right",
            state="readonly",
            readonlybackground="white",
            relief="sunken",
            bd=3,
        )
        self.display.grid(row=0, column=0, columnspan=3, padx=6, pady=(0, 14),
                          ipady=6, sticky="ew")

    def _build_buttons(self):
        for column in range(3):
            self.frame.columnconfigure(column, weight=1, uniform="keys")

        for row, keys in enumerate(KEYPAD, start=1):
            for column, key in enumerate(keys):
                if key in DIGITS:
                    command = partial(self.press_digit, key)
                elif key == "=":
                    command = self.calculate
                else:
                    command = partial(self.press_operator, key)
                self._create_button(key, row, column, command)

        self._create_button("clear", len(KEYPAD) + 1, 0, self.clear)

    def _create_button(self, text, row, column, command):
        button = tk.Button(self.frame, text=text, command=command,
                           font=BUTTON_FONT, width=8, takefocus=False)
        button.grid(row=row, column=column, padx=6, pady=8, ipady=2, sticky="ew")

    # ----- Display -----
    def _refresh(self, text=None):
        self.display_var.set(self.expression if text is None else text)
        self.display.xview_moveto(1)

    def _show_error(self, message):
        self.expression = ""
        self.fresh = True
        self._refresh(message)

    # ----- Button actions -----
    def press_digit(self, char):
        if self.fresh:                      # start a new calculation
            self.expression = ""
            self.fresh = False

        number = re.search(r"[\d.]*$", self.expression).group()  # number being typed
        if char == ".":
            if "." in number:               # only one decimal point per number
                return
            if not number:
                char = "0."
        elif number == "0":                 # avoid leading zeros like 05
            self.expression = self.expression[:-1]

        if len(self.expression) + len(char) <= MAX_LENGTH:
            self.expression += char
        self._refresh()

    def press_operator(self, char):
        expression = self.expression
        if expression == "-" or (not expression and char != "-"):
            return                          # only a leading '-' is allowed on empty input

        self.fresh = False
        if expression and expression[-1] in OPERATORS:
            self.expression = expression[:-1] + char        # replace previous operator
        elif len(expression) < MAX_LENGTH:
            self.expression += char
        self._refresh()

    def calculate(self):
        expression = self.expression.rstrip(OPERATORS)
        if not expression:
            return
        try:
            result = format_result(safe_eval(expression))
        except ZeroDivisionError:
            self._show_error("Cannot divide by 0")
        except Exception:
            self._show_error("Error")
        else:
            self.expression = result
            self.fresh = True
            self._refresh()

    def clear(self):
        self.expression = ""
        self.fresh = False
        self._refresh()

    def backspace(self):
        if self.fresh:
            self.clear()
        else:
            self.expression = self.expression[:-1]
            self._refresh()

    # ----- Keyboard support (digits, . + - * /, Enter, Backspace, Esc) -----
    def on_key(self, event):
        char, key = event.char, event.keysym
        if char in DIGITS or char == ".":
            self.press_digit(char)
        elif char and char in OPERATORS:
            self.press_operator(char)
        elif char == "=" or key in ("Return", "KP_Enter"):
            self.calculate()
        elif key == "BackSpace":
            self.backspace()
        elif key in ("Escape", "Delete") or char in ("c", "C"):
            self.clear()


def main():
    root = tk.Tk()
    Calculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
