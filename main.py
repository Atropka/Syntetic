import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re

# Определяем типы токенов
TOKEN_TYPES = [
    ('FLOAT', r'\d+(\.\d+)?([eE][+-]?\d+)?(?<![eE][eE])'),  # Числа с плавающей точкой
    ('IDEN', r'([A-Za-z_][A-Za-z0-9_]*)'),  # Идентификаторы
    ('ASSIGN', r':='),  # Знак присваивания
    ('ADD', r'\+'),  # Оператор сложения
    ('SUB', r'-'),  # Оператор вычитания
    ('MUL', r'\*'),  # Оператор умножения
    ('DIV', r'/'),  # Оператор деления
    ('LPAREN', r'\('),  # Левая круглая скобка
    ('RPAREN', r'\)'),  # Правая круглая скобка
    ('SEMICOLON', r';'),  # Точка с запятой
    ('WHITESPACE', r'\s+'),  # Пробелы (игнорируем)
    ('DOTDOT', r'\.\.'),  # Две точки подряд (ошибка)
]

# Объединяем регулярные выражения в одно
TOKEN_REGEX = '|'.join(f'(?P<{token_type}>{pattern})' for token_type, pattern in TOKEN_TYPES)
token_regex = re.compile(TOKEN_REGEX)


class SyntaxAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Синтаксический Анализатор Бухтияров_М_А ИС42")

        # Поля ввода
        self.text_input = tk.Text(root, height=30, width=50)
        self.text_input.grid(row=0, column=0, sticky="nswe", padx=(0, 5))

        # Кнопки для управления
        self.button_frame = tk.Frame(root)
        self.button_frame.grid(row=1, column=0, padx=10, pady=5)

        self.load_button = tk.Button(self.button_frame, text="Загрузить файл", command=self.load_from_file)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.analyze_button = tk.Button(self.button_frame, text="Анализировать", command=self.analyze)
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        # Таблица токенов
        self.token_tree = ttk.Treeview(root, columns=("No", "Тип", "Значение"), show="headings")
        self.token_tree.heading("No", text="№")
        self.token_tree.heading("Тип", text="Тип")
        self.token_tree.heading("Значение", text="Значение")
        self.token_tree.grid(row=0, column=1, sticky="nswe", padx=(5, 0))

        # Дерево синтаксического анализа
        self.parse_tree = ttk.Treeview(root)
        self.parse_tree.heading("#0", text="Синтаксическое дерево")
        self.parse_tree.grid(row=0, column=2, padx=10, sticky="nswe")

        # Настройка стиля
        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=2)
        self.root.columnconfigure(2, weight=2)

    def load_from_file(self):
        """Загрузка текста из файла."""
        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_input.delete(1.0, tk.END)
                    self.text_input.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def analyze(self):
        """Запуск анализа."""
        input_text = self.text_input.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showerror("Ошибка", "Пустой ввод")
            return

        try:
            # Лексический анализ
            tokens = self.lexer(input_text)
            if not tokens:
                return
            self.display_tokens(tokens)

            # Синтаксический анализ

            analyzer = SyntaxAnalyzer()
            parse_tree = analyzer.parse(tokens)
            self.display_parse_tree(parse_tree)
        except Exception as e:
            messagebox.showerror("Ошибка анализа", str(e))

    def lexer(self, text):
        """Лексический анализатор."""
        tokens = []
        for match in token_regex.finditer(text):
            token_type = match.lastgroup
            token_value = match.group(token_type)

            if token_type == "WHITESPACE":
                continue  # Пропускаем пробелы

            if token_type == "DOTDOT":
                # Проверяем на две точки подряд
                messagebox.showerror("Ошибка", "Две точки подряд ('..') недопустимы.")
                return []  # Прекращаем лексический анализ

            if token_type == "FLOAT":
                # Проверка на некорректный формат экспоненциальной записи
                if re.search(r'[eE]{2,}', token_value):
                    messagebox.showerror("Ошибка", f"Некорректное число: {token_value} (две 'e' подряд)")
                    return []
                if re.search(r'[eE]$', token_value):
                    messagebox.showerror("Ошибка", f"Некорректное число: {token_value} ('e' без экспоненты)")
                    return []
                if re.search(r'[eE][^+-]?\d+(\.\d+)', token_value):
                    messagebox.showerror("Ошибка",
                                         f"Некорректное число: {token_value} (точка в экспоненциальной части)")
                    return []

            tokens.append((token_type, token_value))

        return tokens

    def display_tokens(self, tokens):
        """Отображение токенов в таблице."""
        for row in self.token_tree.get_children():
            self.token_tree.delete(row)
        for idx, (token_type, token_value) in enumerate(tokens, start=1):
            self.token_tree.insert("", "end", values=(idx, token_type, token_value))

    def display_parse_tree(self, tree, parent=""):
        """Отображение дерева синтаксического анализа."""
        self.parse_tree.delete(*self.parse_tree.get_children())

        def add_node(node, parent, tag=None):
            # Если узел — строка или число, добавляем его как лист дерева
            if isinstance(node, (str, int)):
                return self.parse_tree.insert(parent, "end", text=node)
            # Если узел — кортеж, добавляем его как узел с тегом
            elif isinstance(node, tuple):
                # Используем первый элемент кортежа в качестве тега (например, <S>, <E>)
                tag = node[0] if isinstance(node[0], str) and node[0].startswith("<") else None
                label = tag if tag else "..."
                item = self.parse_tree.insert(parent, "end", text=label)

                # Рекурсивно добавляем дочерние элементы
                for child in node[1:]:
                    add_node(child, item)

        for expr in tree:
            add_node(expr, parent)


class SyntaxAnalyzer:
    def __init__(self):
        self.tokens = []
        self.current = 0

    def parse(self, tokens):
        self.tokens = tokens
        self.current = 0
        expressions = []
        while not self._at_end():
            expressions.append(self._S())
            if not self._at_end() and self.tokens[self.current][0] == "SEMICOLON":
                # Включаем точку с запятой в структуру дерева
                semicolon = self.tokens[self.current][1]
                self.current += 1
                expressions[-1] = (
                "<S>", expressions[-1], semicolon)  # Добавляем точку с запятой к последнему выражению
        return expressions

    def _S(self):
        if self._at_end():
            raise Exception("Ошибка ввода")

        if self.tokens[self.current][0] == "IDEN":
            iden = self.tokens[self.current][1]
            self.current += 1
            if not self._at_end() and self.tokens[self.current][0] == "ASSIGN":
                self.current += 1
                expr = self._E()
                return ("<S>", iden, ":=", expr)

            expr = self._E()
            return ("<S>", iden, expr)

        expr = self._E()
        return ("<S>", expr)

    def _E(self):
        left = self._T()
        while not self._at_end() and self.tokens[self.current][0] in {"ADD", "SUB"}:
            op = self.tokens[self.current][1]
            self.current += 1

            # Проверяем, что после оператора идет валидный фактор
            if self._at_end() or self.tokens[self.current][0] not in {"IDEN", "FLOAT", "LPAREN"}:
                raise Exception(
                    f"Ожидалось значение после оператора '{op}', но найдено '{self.tokens[self.current][1]}'")

            right = self._F()
            left = ("<E>", left, op, right)
        return left

    def _T(self):
        left = self._F()
        while not self._at_end() and self.tokens[self.current][0] in {"MUL", "DIV"}:
            op = self.tokens[self.current][1]
            self.current += 1

            if self._at_end() or self.tokens[self.current][0] not in {"IDEN", "FLOAT", "LPAREN"}:
                raise Exception(
                    f"Ожидалось значение после оператора '{op}', но найдено '{self.tokens[self.current][1]}'")
            right = self._F()
            left = ("<E>", left, op, right)
        return left

    def _F(self):
        if self._at_end():
            raise Exception("Ошибка ввода")

        if self.tokens[self.current][0] == "RPAREN":
            # Если встречается закрывающая скобка без открывающей
            raise Exception("Ошибка: Найдена закрывающая скобка без соответствующей открывающей")

        if self.tokens[self.current][0] == "LPAREN":
            self.current += 1
            expr = self._E()
            if not self._at_end() and self.tokens[self.current][0] == "RPAREN":
                self.current += 1
                return ("<E>", "(", expr, ")")
            else:
                raise Exception("Ошибка: Ожидалась закрывающая скобка")

        elif self.tokens[self.current][0] in {"IDEN", "FLOAT"}:
            value = self.tokens[self.current][1]
            self.current += 1
            return ("<E>", value)



    def _at_end(self):
        return self.current >= len(self.tokens)


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = SyntaxAnalyzerApp(root)
    root.mainloop()
