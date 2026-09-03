"""Правиловый (fallback) бэкенд — работает без модели.

Используется, чтобы проверить весь конвейер (промпт -> JSON -> GDScript),
когда GGUF-веса недоступны, и как эталонный ответ для сравнения качества.
Маппит ключевые слова из идеи игрока на валидные значения схемы.
"""

import json

from ..core.schema import GameIntent
from ..core.prompter import build_prompt

# Ключевые слова -> значения схемы
KEYWORDS = {
    "genre": {
        "platformer": ["platformer", "платформер", "run and jump", "прыга"],
        "puzzle": ["puzzle", "пазл", "головоломк", "match"],
        "runner": ["runner", "раннер", "бег"],
        "twin_stick": ["twin", "шутер", "shooter", "twin stick"],
        "clicker": ["clicker", "кликер", "tap"],
        "top_down": ["top down", "вид сверху", "сверху"],
    },
    "level_type": {
        "side_scroll": ["side", "сайд", "горизонт"],
        "top_down": ["top down", "сверху"],
        "fixed_arena": ["arena", "арена", "fixed"],
        "vertical": ["vertical", "вертикал", "falling"],
    },
    "player_movement": {
        "left_right_jump": ["jum", "прыг", "jump"],
        "left_right": ["run", "бег", "двига"],
        "free_2d": ["free", "свободн"],
        "static": ["static", "стои", "fixed"],
    },
    "player_shoot": {
        "bullet": ["shoot", "стрел", "bullet"],
        "auto_aim": ["auto", "aim", "самонавед"],
        "none": [],
    },
    "enemy_behavior": {
        "chase": ["chase", "гоня", "преслед"],
        "patrol": ["patrol", "патрул"],
        "shoot": ["shoot", "стрел"],
        "static": [],
    },
    "enemy_kind": {
        "walker": ["walker", "ход"],
        "flyer": ["fly", "лет"],
        "turret": ["turret", "турел"],
        "boss": ["boss", "босс"],
    },
    "color_scheme": {
        "retro": ["retro", "ретро", "pixel", "пиксел"],
        "neon": ["neon", "неон"],
        "pastel": ["pastel", "пастел", "soft"],
        "mono": ["mono", "монохром", "black and white"],
    },
    "ui": {
        "score": ["score", "очк", "счёт", "очки"],
        "lives": ["lives", "жизн"],
        "health": ["health", "здоров", "hp"],
        "timer": ["timer", "врем", "тайм"],
        "level": ["level", "уровн"],
    },
    "mechanics": {
        "jump": ["jump", "прыг"],
        "gravity": ["gravity", "гравит"],
        "collision": ["collision", "столкнов", "hit"],
        "win_goal": ["win", "побед", "goal", "цель", "финиш"],
        "timer": ["timer", "врем"],
        "score_gain": ["score", "очк", "балл"],
    },
}


def _match_group(text: str, mapping: dict) -> str | None:
    for value, words in mapping.items():
        if any(w in text for w in words):
            return value
    return None


def _required_group(text: str, mapping: dict, default: str) -> str:
    return _match_group(text, mapping) or default


class RuleBackend:
    name = "rule"

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        """Игнорирует промпт, эвристически строит манифест по USER-тексту."""
        # Промпт содержит "Player idea: <text>". Достаём его.
        user_text = prompt.split("Player idea:", 1)[-1].split("\nJSON:", 1)[0]
        t = user_text.lower()

        raw = {
            "genre": _required_group(t, KEYWORDS["genre"], "platformer"),
            "level_type": _required_group(t, KEYWORDS["level_type"], "side_scroll"),
            "player_movement": _required_group(t, KEYWORDS["player_movement"],
                                               "left_right"),
            "player_shoot": _match_group(t, KEYWORDS["player_shoot"]) or "none",
            "enemy_behavior": _match_group(t, KEYWORDS["enemy_behavior"]) or "patrol",
            "enemy_kind": _match_group(t, KEYWORDS["enemy_kind"]) or "walker",
            "color_scheme": _required_group(t, KEYWORDS["color_scheme"], "retro"),
            "ui": [k for k, words in KEYWORDS["ui"].items()
                   if any(w in t for w in words)] or ["score"],
            "mechanics": [k for k, words in KEYWORDS["mechanics"].items()
                          if any(w in t for w in words)] or ["collision"],
            "players": 1,
            "enemies": 1,
            "difficulty": 2,
        }
        return json.dumps(raw, ensure_ascii=False)

    def __repr__(self) -> str:
        return "<rule fallback backend>"


def build_prompt_for_rule(user_text: str) -> str:
    """Обёртка для обратной совместимости."""
    return build_prompt(user_text)
