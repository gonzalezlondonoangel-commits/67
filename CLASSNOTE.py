# CLASSNOTE - Calculadora matemática
# Hecha con dedicación por Ángel
# Requiere Kivy instalado en Pydroid 3.
#
# Funciones: +, -, *, /, paréntesis e implicit multiplication (5(7)),
# porcentajes (20%), promedio(...), raíz(...), sqrt(...), potencias (**),
# y lógica con not, and, or y comparaciones.
#
# IMPORTANTE: este archivo es una aplicación Kivy para ejecutar en Pydroid 3.
# Para crear un APK instalable, después hay que compilar el proyecto con una
# herramienta de construcción Android; subir el .py a GitHub por sí solo no crea un APK.

import ast
import math
import re
import operator as op

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

# Colores RGB normalizados: fondo azul eléctrico, números amarillos,
# bordes rojos y detalles negros.
AZUL = (0.02, 0.16, 0.95, 1)
AMARILLO = (1, 0.88, 0.05, 1)
ROJO = (0.95, 0.04, 0.08, 1)
NEGRO = (0.025, 0.025, 0.04, 1)
BLANCO = (1, 1, 1, 1)

BIN_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}
UNARY_OPS = {ast.UAdd: op.pos, ast.USub: op.neg, ast.Not: op.not_}
CMP_OPS = {
    ast.Eq: op.eq, ast.NotEq: op.ne, ast.Lt: op.lt,
    ast.LtE: op.le, ast.Gt: op.gt, ast.GtE: op.ge,
}
FUNCTIONS = {
    "raiz": math.sqrt,
    "sqrt": math.sqrt,
    "abs": abs,
    "promedio": lambda *xs: sum(xs) / len(xs) if xs else 0,
    "prom": lambda *xs: sum(xs) / len(xs) if xs else 0,
    "porcentaje": lambda x, total: (x / 100) * total,
}


def preparar_expresion(expression):
    """Convierte expresiones de usuario a una forma que Python puede analizar."""
    s = expression.strip().lower()
    s = s.replace("×", "*").replace("÷", "/").replace("−", "-")
    s = s.replace("^", "**")
    # 20% se interpreta como 20/100. Para módulo, se puede escribir mod(a,b)
    # no está habilitado; el operador % queda disponible dentro de expresiones.
    s = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)\s*%", r"(\1/100)", s)
    # Multiplicación implícita: 5(7), 2(3+1), (2+3)(4).
    s = re.sub(r"(\d|\))\s*\(", r"\1*(", s)
    # Permite escribir "mod" no se agrega como función para mantenerlo simple.
    return s


def evaluar_nodo(node):
    """Evaluador restringido: no ejecuta código arbitrario."""
    if isinstance(node, ast.Expression):
        return evaluar_nodo(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, bool)):
        return node.value
    if isinstance(node, ast.Num):  # compatibilidad con algunas versiones de Python
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left, right = evaluar_nodo(node.left), evaluar_nodo(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError("No se puede dividir entre cero.")
        return BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](evaluar_nodo(node.operand))
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = evaluar_nodo(value)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = evaluar_nodo(value)
                if result:
                    return result
            return result
    if isinstance(node, ast.Compare):
        left = evaluar_nodo(node.left)
        for cmp, comparator in zip(node.ops, node.comparators):
            right = evaluar_nodo(comparator)
            if type(cmp) not in CMP_OPS or not CMP_OPS[type(cmp)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id.lower()
        if name not in FUNCTIONS:
            raise ValueError("Función no reconocida. Usa raiz(), promedio() o porcentaje().")
        args = [evaluar_nodo(arg) for arg in node.args]
        return FUNCTIONS[name](*args)
    if isinstance(node, ast.Name) and node.id.lower() in ("true", "verdadero"):
        return True
    if isinstance(node, ast.Name) and node.id.lower() in ("false", "falso"):
        return False
    raise ValueError("La expresión contiene algo que la calculadora no admite.")


def calcular(expression):
    prepared = preparar_expresion(expression)
    tree = ast.parse(prepared, mode="eval")
    return evaluar_nodo(tree)


class ClassNoteApp(App):
    title = "CLASSNOTE"

    def build(self):
        Window.clearcolor = AZUL
        Window.softinput_mode = "below_target"

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(76),
                           padding=dp(8), spacing=dp(10))
        # Logo sencillo: fondo rojo con A azul vivo y + blanco.
        logo = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(90),
                         padding=dp(5), spacing=dp(1))
        from kivy.graphics import Color, RoundedRectangle
        with logo.canvas.before:
            Color(*ROJO)
            logo.bg_rect = RoundedRectangle(pos=logo.pos, size=logo.size, radius=[dp(10)])
        logo.bind(pos=lambda w, p: setattr(w.bg_rect, "pos", p),
                  size=lambda w, s: setattr(w.bg_rect, "size", s))
        logo.add_widget(Label(text="[b]A[/b]", markup=True, color=AZUL,
                              font_size="38sp", bold=True))
        logo.add_widget(Label(text="[b]+[/b]", markup=True, color=BLANCO,
                              font_size="34sp", bold=True))
        header.add_widget(logo)

        welcome = Label(
            text="[b]CLASSNOTE[/b]\nAdelante, bienvenido a CLASSNOTE, una app matemática hecha con dedicación por Ángel para el cálculo de tus problemas.",
            markup=True, color=AMARILLO, font_size="15sp", halign="left",
            valign="middle"
        )
        welcome.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(welcome)
        root.add_widget(header)

        self.display = TextInput(
            hint_text="Ingrese amablemente tu número o expresión…",
            multiline=False, font_size="22sp", size_hint_y=None, height=dp(58),
            background_color=NEGRO, foreground_color=AMARILLO,
            cursor_color=BLANCO, hint_text_color=(0.8, 0.8, 0.8, 1),
            padding=[dp(12), dp(14), dp(12), dp(10)]
        )
        root.add_widget(self.display)

        self.result_label = Label(
            text="Resultado: listo para calcular", color=AMARILLO,
            font_size="18sp", size_hint_y=None, height=dp(42),
            halign="left", valign="middle"
        )
        self.result_label.bind(size=lambda w, s: setattr(w, "text_size", s))
        root.add_widget(self.result_label)

        scroll = ScrollView()
        keypad = GridLayout(cols=4, spacing=dp(6), padding=dp(2),
                            size_hint_y=None)
        keypad.bind(minimum_height=keypad.setter("height"))

        keys = [
            ("AC", "DEL", "(", ")"),
            ("7", "8", "9", "÷"),
            ("4", "5", "6", "×"),
            ("1", "2", "3", "−"),
            ("0", ".", "%", "+"),
            ("^", "√", "=", "/"),
            ("and", "or", "not", ">"),
            ("<", ">=", "==", "!="),
        ]
        for row in keys:
            for key in row:
                btn = Button(
                    text=key, font_size="20sp", bold=True,
                    color=AMARILLO if key not in ("=", "AC", "DEL") else BLANCO,
                    background_normal="", background_color=NEGRO,
                    size_hint_y=None, height=dp(55)
                )
                # Marco rojo alrededor de cada tecla.
                with btn.canvas.after:
                    Color(*ROJO)
                    from kivy.graphics import Line
                    btn.border_line = Line(rectangle=(btn.x, btn.y, btn.width, btn.height),
                                           width=1.5)
                btn.bind(pos=lambda w, p: setattr(w.border_line, "rectangle",
                                                   (w.x, w.y, w.width, w.height)),
                         size=lambda w, s: setattr(w.border_line, "rectangle",
                                                    (w.x, w.y, w.width, w.height)))
                btn.bind(on_release=lambda instance, value=key: self.press(value))
                keypad.add_widget(btn)

        extra = [
            ("promedio(", "Promedio: promedio(5,7,9)"),
            ("raiz(", "Raíz cuadrada: raiz(81)"),
            ("porcentaje(", "Porcentaje de una cantidad: porcentaje(15,200)"),
            ("**", "Potencia: 2**5"),
        ]
        for value, label in extra:
            btn = Button(text=value, font_size="16sp", color=AMARILLO,
                         background_normal="", background_color=NEGRO,
                         size_hint_y=None, height=dp(48))
            with btn.canvas.after:
                Color(*ROJO)
                from kivy.graphics import Line
                btn.border_line = Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=1.5)
            btn.bind(pos=lambda w, p: setattr(w.border_line, "rectangle",
                                               (w.x, w.y, w.width, w.height)),
                     size=lambda w, s: setattr(w.border_line, "rectangle",
                                                (w.x, w.y, w.width, w.height)))
            btn.bind(on_release=lambda instance, v=value: self.insert_text(v))
            keypad.add_widget(btn)

        scroll.add_widget(keypad)
        root.add_widget(scroll)

        help_label = Label(
            text="Ejemplos: 5(7)  •  2+(4×7)÷8  •  20%  •  not(40 or 23>9 and 6)",
            color=BLANCO, font_size="12sp", size_hint_y=None, height=dp(34)
        )
        root.add_widget(help_label)
        return root

    def insert_text(self, value):
        self.display.text += value
        self.display.focus = True

    def press(self, key):
        if key == "AC":
            self.display.text = ""
            self.result_label.text = "Resultado: listo para calcular"
        elif key == "DEL":
            self.display.text = self.display.text[:-1]
        elif key == "=":
            self.solve()
        else:
            mapping = {"×": "*", "÷": "/", "−": "-", "√": "raiz("}
            self.insert_text(mapping.get(key, key))

    def solve(self):
        expression = self.display.text.strip()
        if not expression:
            self.result_label.text = "Ingrese amablemente tu número o expresión."
            return
        try:
            result = calcular(expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self.result_label.text = "Resultado: " + str(result)
            print("CLASSNOTE | expresión:", expression, "| resultado:", result)
        except ZeroDivisionError as exc:
            self.result_label.text = str(exc)
        except Exception as exc:
            self.result_label.text = "Revisa la expresión: " + str(exc)


if __name__ == "__main__":
    ClassNoteApp().run()
