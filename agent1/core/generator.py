"""Генератор GDScript-скелета из GameIntent.

Безопасный слой: даже если tiny-модель вернула кривой JSON/brief, мы
выдаём детерминированный шаблон и сообщаем о нормализации. Модель НЕ пишет
произвольный код — она лишь заполняет валидные поля схемы.
"""

from ..core.schema import GameIntent
from ..core.prompter import extract_json


def _num(raw: dict, key: str, default: int, lo: int, hi: int) -> int:
    try:
        v = int(raw.get(key, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def render_skeleton(intent: GameIntent) -> str:
    """Возвращает текст .gd файла под манифест."""
    viz = {
        "genre": intent.get("genre", "platformer"),
        "level_type": intent.get("level_type", "side_scroll"),
        "player_movement": intent.get("player_movement", "left_right"),
        "enemy_behavior": intent.get("enemy_behavior", "patrol"),
        "lives": intent.get("players", 1) * 3,
        "difficulty": intent.get("difficulty", 2),
        "enemies": intent.get("enemies", 3),
        "ui": ", ".join(sorted(intent.get("ui", ["score"]))) or "score",
        "mechanics": ", ".join(sorted(intent.get("mechanics", []))) or "none",
    }
    with open(_template_path(), encoding="utf-8") as fh:
        template = fh.read()
    return template.format(**viz)


def _template_path() -> str:
    import os
    return os.path.join(os.path.dirname(__file__),
                        "..", "templates", "game_skeleton.gd")


def manifest_from_model_output(raw_output: str,
                               default_intent: GameIntent | None = None) -> GameIntent:
    """Собирает валидный GameIntent из вывода модели. При сбое — default."""
    try:
        data = extract_json(raw_output)
        intent = GameIntent.from_dict(data)
        if not intent.is_valid and default_intent is not None:
            intent = default_intent
        return intent
    except ValueError:
        return default_intent if default_intent is not None else GameIntent()


__all__ = ["render_skeleton", "manifest_from_model_output", "extract_json"]
