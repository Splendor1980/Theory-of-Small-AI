"""Тема/настройка шаблонов: «логика + тема» (stdlib-only).

Отвечает на запросы вида:
  - «шашки/фишки как кошки и собаки»
  - «меняй кристаллы на конфеты»
  - «neon», «тёмный фон», «шрифт полинял»
Меняет ВНЕШНИЙ ВИД и текст, НЕ трогая механики игры.

Любой шаблон может объявить произвольные плейсхолдеры {{THEME_*}}
(например {{THEME_TITLE}}, {{THEME_COLOR_BALL}}, {{THEME_COLOR_SNAKE}}).
Библиотека сканирует код, находит эти токены и подставляет значения из
выбранной темы-пресета. Неизвестный токен тип-по умолчанию (цвет крупно).
Тема = словарь значений для подстановки.
"""
import re

_TOKEN_RE = re.compile(r"\{\{THEME_([A-Z_0-9]+)\}\}")


class Themes(dict):
    """Словарь пресетов; недостающий ключ возвращает нейтральное значение."""
    _DEFAULTS = {
        "TITLE": "Игра",
        "MARK_X": "X",
        "MARK_O": "O",
    }

    def __getitem__(self, key):
        v = dict.get(self, key)
        if v is None:
            if key in self._DEFAULTS:
                return self._DEFAULTS[key]
            # любой *цвет* по умолчанию — нейтральный белый
            if key.startswith("COLOR_"):
                return "1, 1, 1, 1"
            # остальное — просто ключ как заглушка
            return key
        return v


# Пресе: имя темы -> значения для плейсхолдеров {{THEME_*}}.
# Поле с нейтральным значением можно опускать — подставится default.
PRESETS = {
    "classic": Themes({
        "TITLE": "Классика",
        "MARK_X": "X", "MARK_O": "O",
        "COLOR_X": "1, 0.43, 0.43, 1", "COLOR_O": "0.36, 0.62, 1, 1",
        "COLOR_GRID": "1, 1, 1, 0.6", "COLOR_WIN": "0.36, 1, 0.36, 1",
        "BG": "0.12, 0.12, 0.15, 1",
        "COLOR_PADDLE_L": "1, 0.43, 0.43, 1", "COLOR_PADDLE_R": "0.36, 0.62, 1, 1",
        "COLOR_BALL": "0.95, 0.95, 0.9, 1", "COLOR_NET": "1, 1, 1, 0.5",
        "COLOR_SNAKE": "0.3, 0.9, 0.3, 1", "COLOR_FOOD": "0.95, 0.3, 0.3, 1",
        "COLOR_SNAKE_HEAD": "0.2, 0.8, 0.2, 1",
    }),
    "neon": Themes({
        "TITLE": "Неон",
        "MARK_X": "X", "MARK_O": "O",
        "COLOR_X": "0, 1, 1, 1", "COLOR_O": "1, 0.2, 1, 1",
        "COLOR_GRID": "0.3, 1, 1, 0.8", "COLOR_WIN": "0, 1, 0.5, 1",
        "BG": "0.02, 0.02, 0.08, 1",
        "COLOR_PADDLE_L": "0, 1, 1, 1", "COLOR_PADDLE_R": "1, 0.2, 1, 1",
        "COLOR_BALL": "1, 1, 0.2, 1", "COLOR_NET": "0, 1, 1, 0.6",
        "COLOR_SNAKE": "0, 1, 0.9, 1", "COLOR_FOOD": "1, 0.2, 1, 1",
        "COLOR_SNAKE_HEAD": "0, 0.8, 1, 1",
    }),
    "candy": Themes({
        "TITLE": "Конфеты",
        "MARK_X": "X", "MARK_O": "O",
        "COLOR_X": "1, 0.6, 0.9, 1", "COLOR_O": "0.6, 1, 0.7, 1",
        "COLOR_GRID": "1, 0.9, 0.95, 0.7", "COLOR_WIN": "1, 0.85, 0.3, 1",
        "BG": "0.25, 0.15, 0.3, 1",
        "COLOR_PADDLE_L": "1, 0.6, 0.9, 1", "COLOR_PADDLE_R": "0.6, 1, 0.7, 1",
        "COLOR_BALL": "1, 0.85, 0.3, 1", "COLOR_NET": "1, 0.9, 0.95, 0.7",
        "COLOR_SNAKE": "1, 0.6, 0.9, 1", "COLOR_FOOD": "1, 0.85, 0.3, 1",
        "COLOR_SNAKE_HEAD": "0.9, 0.4, 0.8, 1",
    }),
    "cats_dogs": Themes({
        "TITLE": "Кошки против собак",
        "MARK_X": "X", "MARK_O": "O",
        "COLOR_X": "0.9, 0.5, 0.2, 1", "COLOR_O": "0.5, 0.3, 0.1, 1",
        "COLOR_GRID": "0.95, 0.85, 0.7, 0.8", "COLOR_WIN": "0.3, 0.9, 0.4, 1",
        "BG": "0.2, 0.25, 0.18, 1",
        "COLOR_PADDLE_L": "0.9, 0.5, 0.2, 1", "COLOR_PADDLE_R": "0.5, 0.3, 0.1, 1",
        "COLOR_BALL": "0.95, 0.85, 0.7, 1", "COLOR_NET": "0.95, 0.85, 0.7, 0.7",
        "COLOR_SNAKE": "0.9, 0.5, 0.2, 1", "COLOR_FOOD": "0.5, 0.3, 0.1, 1",
        "COLOR_SNAKE_HEAD": "0.85, 0.4, 0.15, 1",
    }),
    "ocean": Themes({
        "TITLE": "Океан",
        "MARK_X": "X", "MARK_O": "O",
        "COLOR_X": "0.4, 0.9, 1, 1", "COLOR_O": "1, 0.9, 0.4, 1",
        "COLOR_GRID": "0.6, 0.8, 1, 0.7", "COLOR_WIN": "1, 0.7, 0.2, 1",
        "BG": "0.02, 0.1, 0.2, 1",
        "COLOR_PADDLE_L": "0.4, 0.9, 1, 1", "COLOR_PADDLE_R": "1, 0.9, 0.4, 1",
        "COLOR_BALL": "0.8, 1, 1, 1", "COLOR_NET": "0.6, 0.8, 1, 0.7",
        "COLOR_SNAKE": "0.3, 0.8, 1, 1", "COLOR_FOOD": "1, 0.7, 0.2, 1",
        "COLOR_SNAKE_HEAD": "0.2, 0.6, 1, 1",
    }),
}

# ключевые слова -> тема
KEYWORDS = {
    "cats_dogs": ["кот", "кошк", "собак", "пёс", "cat", "dog", "шашк как", "фишк как"],
    "candy": ["конфет", "candy", "сладк", "кристал", "sweets"],
    "neon": ["neon", "неон", "неонов"],
    "ocean": ["ocean", "океан", "морск", "deep sea", "underwater"],
}


def pick_theme(idea):
    """Выбрать тему по идее. Вернуть (имя_темы, Themes-пресет)."""
    t = (idea or "").lower()
    for name, words in KEYWORDS.items():
        if any(w in t for w in words):
            return name, PRESETS[name]
    return "classic", PRESETS["classic"]


def tokens_in(code):
    """Вернуть множество токенов {{THEME_X}} из кода (X — без THEME_)."""
    return set(_TOKEN_RE.findall(code))


def apply_theme(code, theme=None, idea=None):
    """Подставить тему в код шаблона: заполнить все встреченные {{THEME_*}}."""
    if theme is None:
        _, theme = pick_theme(idea or "")
    def repl(m):
        key = m.group(1)
        return str(theme[key])
    out = _TOKEN_RE.sub(repl, code)
    return out
