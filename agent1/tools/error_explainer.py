"""Переводчик ошибок Godot -> человеческая инструкция (stdlib-only).

Микро-модель/правила тонут в сырых логах вида:
    Parser Error: Identifier "speed" not declared in current scope.
Здесь регексы превращают технический лог в прямое руководство к действию,
понятное малой модели. Это сокращает число итераций feedback-loop с 10-15 до 1-2.

Pattern -> (regex, human_instruction, category)
"""
import re

# Порядок важен: более специфичные паттерны раньше.
PATTERNS = [
    (
        re.compile(r'Identifier "([^"]+)" not declared', re.I),
        'Ты использовал переменную "{}", но не объявил её выше в файле. '
        'Добавь "var {}" (или "export var {}") до её первого использования.',
        "undeclared_var",
    ),
    (
        re.compile(r'(Invalid|Unknown) identifier "([^"]+)"', re.I),
        'Ссылка "{}" не определена в текущей области видимости. '
        "Проверь имя (регистр важен) и объяви её до использования.",
        "unknown_id",
    ),
    (
        re.compile(r"Parser Error:\s*(.+)", re.I),
        "Синтаксическая ошибка парсера: {} . Проверь точку с запятой, "
        "кавычки и структуру блока.",
        "parser",
    ),
    (
        re.compile(r"(Expected )?(one of )?([\w]+)( or [\w]+)*", re.I),
        "Синтаксис: ожидался токен. Проверь скобки и ключевые слова в этой строке.",
        "syntax_token",
    ),
    (
        re.compile(r"Unclosed (string|parenthesis|block)", re.I),
        "Незакрытая {}: проверь парность скобок/кавычек.",
        "unclosed",
    ),
    (
        re.compile(r"(Cannot|Could not) open file[\s:]+(.+)", re.I),
        "Не найден файл/путь: {} . Проверь путь к ресурсу.",
        "io",
    ),
    (
        re.compile(r"Parse Error: (Expected [\w \"]+)", re.I),
        "Синтаксис: {} . Проверь структуру строки.",
        "parse",
    ),
    (
        re.compile(r"([A-Za-z_]\w*):\s*Error:\s*(.+)", re.I),
        "Ошибка в строке/функции: {} - {} .",
        "generic",
    ),
]


class ErrorExplainer:
    def __init__(self, max_repeat=3):
        self.repeat_guard = {}   # normalized_error -> counter
        self.max_repeat = max_repeat

    def explain(self, raw_log):
        """Сырой лог -> (человеческая_инструкция, категория) или (None, None)."""
        if not raw_log or not str(raw_log).strip():
            return None, None
        text = str(raw_log).strip()
        for pattern, human, category in PATTERNS:
            m = pattern.search(text)
            if m:
                groups = [g for g in m.groups() if g]
                try:
                    instruction = human.format(*groups, *([""] * 4))
                except (IndexError, KeyError):
                    instruction = human
                return instruction, category
        return text, "raw"

    def is_looping(self, raw_log):
        """True, если та же ошибка повторилась слишком много раз (зацикливание)."""
        key = str(raw_log).strip()[:120]
        n = self.repeat_guard.get(key, 0) + 1
        self.repeat_guard[key] = n
        return n > self.max_repeat

    def reset(self):
        self.repeat_guard.clear()