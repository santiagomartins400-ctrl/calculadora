"""
Calculadora que corre em segundo plano (ícone na barra de tarefas / bandeja do sistema).

- Ao fechar a janela, a calculadora fica escondida e continua ativa no ícone da bandeja.
- Clique no ícone (ou botão direito > Mostrar) para a voltar a abrir.
- Botão direito > Sair para a fechar completamente.

Dependências:
    pip install pystray pillow

Executar (Windows, sem consola):
    pythonw calculadora_segundo_plano.py
"""

import ast
import operator as op
import queue
import threading
import tkinter as tk

import pystray
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# Avaliação segura de expressões (sem usar eval)
# ---------------------------------------------------------------------------

OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_eval(expression: str):
    """Avalia uma expressão aritmética simples de forma segura."""

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left, right = _eval(node.left), _eval(node.right)
            # Evita potências gigantes que bloqueariam a aplicação
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Expoente demasiado grande")
            return OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("Expressão inválida")

    tree = ast.parse(expression, mode="eval")
    return _eval(tree)


def format_result(value) -> str:
    """Mostra inteiros sem casas decimais e limita os decimais a 12 algarismos."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.12g}"
    return str(value)


# ---------------------------------------------------------------------------
# Interface da calculadora
# ---------------------------------------------------------------------------

BG = "#1e1e1e"
BTN_BG = "#2d2d2d"
BTN_OP_BG = "#3b3b3b"
BTN_EQ_BG = "#0a84ff"
FG = "white"

BUTTONS = [
    ["C", "(", ")", "⌫"],
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "-"],
    ["0", ".", "^", "+"],
    ["="],
]

SYMBOL_TO_PY = {"×": "*", "÷": "/", "^": "**", ",": "."}


class Calculator:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Calculadora")
        root.configure(bg=BG)
        root.resizable(False, False)

        # Fechar a janela só a esconde (a app continua na bandeja)
        root.protocol("WM_DELETE_WINDOW", root.withdraw)

        self.var = tk.StringVar()
        self.display = tk.Entry(
            root,
            textvariable=self.var,
            font=("Segoe UI", 22),
            justify="right",
            bd=0,
            bg=BG,
            fg=FG,
            insertbackground=FG,
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew",
                          padx=10, pady=(12, 8), ipady=12)

        # Atalhos de teclado
        self.display.bind("<Return>", lambda e: self.press("="))
        self.display.bind("<KP_Enter>", lambda e: self.press("="))
        self.display.bind("<Escape>", lambda e: self.press("C"))
        self.display.focus_set()

        for r, row in enumerate(BUTTONS, start=1):
            c = 0
            for label in row:
                span = 4 if label == "=" else 1
                bg = BTN_EQ_BG if label == "=" else (
                    BTN_OP_BG if label in "÷×-+^C⌫()" else BTN_BG)
                tk.Button(
                    root,
                    text=label,
                    font=("Segoe UI", 16),
                    bg=bg,
                    fg=FG,
                    activebackground="#555555",
                    activeforeground=FG,
                    bd=0,
                    height=2,
                    width=5,
                    command=lambda v=label: self.press(v),
                ).grid(row=r, column=c, columnspan=span,
                       sticky="nsew", padx=4, pady=4)
                c += span

        for col in range(4):
            root.columnconfigure(col, weight=1)

    def press(self, label: str):
        current = self.var.get()

        if label == "C":
            self.var.set("")
        elif label == "⌫":
            if current.startswith("Erro"):
                self.var.set("")
            else:
                self.display.delete(len(current) - 1, tk.END) if current else None
        elif label == "=":
            self.evaluate()
        else:
            # Depois de um erro, começa de novo
            if current.startswith("Erro"):
                self.var.set("")
            self.display.insert(tk.INSERT, label)

    def evaluate(self):
        text = self.var.get()
        for symbol, py in SYMBOL_TO_PY.items():
            text = text.replace(symbol, py)

        if not text.strip():
            return
        try:
            result = safe_eval(text)
            self.var.set(format_result(result))
        except ZeroDivisionError:
            self.var.set("Erro: divisão por zero")
        except Exception:
            self.var.set("Erro")
        self.display.icursor(tk.END)


# ---------------------------------------------------------------------------
# Ícone na bandeja do sistema
# ---------------------------------------------------------------------------

def make_tray_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), BG)
    draw = ImageDraw.Draw(img)
    # Símbolo "=" simples
    draw.rectangle((14, 20, 50, 26), fill="white")
    draw.rectangle((14, 36, 50, 42), fill="white")
    return img


def main():
    root = tk.Tk()
    calc = Calculator(root)

    # A queue serve para o ícone da bandeja (outra thread) comunicar
    # com a interface (thread principal), que é a única segura para tkinter.
    commands: queue.Queue = queue.Queue()

    def on_show(icon, item):
        commands.put("show")

    def on_quit(icon, item):
        commands.put("quit")

    tray = pystray.Icon(
        "calculadora",
        make_tray_image(),
        "Calculadora",
        menu=pystray.Menu(
            pystray.MenuItem("Mostrar", on_show, default=True),
            pystray.MenuItem("Sair", on_quit),
        ),
    )
    threading.Thread(target=tray.run, daemon=True).start()

    def show_window():
        root.deiconify()
        root.lift()
        root.focus_force()
        calc.display.focus_set()

    def poll():
        try:
            while True:
                cmd = commands.get_nowait()
                if cmd == "show":
                    show_window()
                elif cmd == "quit":
                    tray.stop()
                    root.destroy()
                    return
        except queue.Empty:
            pass
        root.after(100, poll)

    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
