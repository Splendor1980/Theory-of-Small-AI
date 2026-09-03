"""Библиотека играбельных шаблонов + роутер идей (stdlib-only).

Для ограниченного набора простых игр мы заранее храним ПОЛНЫЕ играбельные
шаблоны (не скелеты с <HAND>). Роутер сопоставляет идею пользователя с
шаблоном по ключевым словам. Если совпадения нет - выдаёт generic-скелет.

Это и есть честный эксперимент: без мини-LLM и без pip, на stdlib,
мы закрываем простые игры (крестики-нолики, пинг-понг, змейка) до
реально играбельного MVP.
"""
import os


def _templates_dir():
    return os.path.join(os.path.dirname(__file__), "..", "templates")


# имя шаблона -> (список ключевых слов-триггеров)
ROUTER = {
    "tic_tac_toe": [
        "tic tac toe", "крестики нолики", "крестики-нолики", "noughts",
        "x and o", "икс и о", "крест", "нолик", "tic tac",
    ],
    "pong": [
        "pong", "понг", "пинг понг", "ping pong", "ракетки", "теннис",
    ],
    "snake": [
        "snake", "змейка", "змея", "snakes",
    ],
}

# человекочитаемые имена для вывода
LABELS = {
    "tic_tac_toe": "Крестики-нолики (играбельный MVP)",
    "pong": "Пинг-понг (шаблон готов, MVP)",
    "snake": "Змейка (шаблон готов, MVP)",
}


def route(idea):
    """Вернуть имя шаблона по идее или None."""
    t = idea.lower()
    for name, words in ROUTER.items():
        for w in words:
            if w in t:
                return name
    return None


def resolve_template(idea):
    """Вернуть (имя_шаблона_или_None, содержимое_файла_или_None)."""
    name = route(idea)
    if not name:
        return None, None
    path = os.path.join(_templates_dir(), name + ".gd")
    if not os.path.exists(path):
        return name, None
    with open(path, encoding="utf-8") as fh:
        return name, fh.read()


def template_label(idea):
    name = route(idea)
    if name:
        return LABELS.get(name, name)
    return None