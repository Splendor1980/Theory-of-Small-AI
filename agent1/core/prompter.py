"""Сборка промпта для tiny LLM.

Маленькая модель (527k) перегружается свободным текстом. Поэтому мы даём ей
жёсткую схему: она должна заполнить JSON по шаблону, а не писать прозу.
Это резко повышает процент «валидных» ответов. Либеральный свободный текст
идёт в поле "game_brief" и игнорируется генератором.
"""

import json


SYSTEM_PROMPT = (
    "You are a compact game-design tool. Respond ONLY with a JSON object "
    "matching this exact schema. Do not add prose or markdown.\n"
    "Schema:\n"
    "  {\n"
    '    "genre": "platformer|puzzle|runner|twin_stick|clicker|top_down",\n'
    '    "player_movement": "left_right|left_right_jump|free_2d|static",\n'
    '    "player_shoot": "none|bullet|auto_aim",\n'
    '    "enemy_behavior": "patrol|chase|static|shoot",\n'
    '    "enemy_kind": "walker|flyer|turret|boss",\n'
    '    "level_type": "side_scroll|top_down|fixed_arena|vertical",\n'
    '    "color_scheme": "retro|neon|pastel|mono",\n'
    '    "ui": ["score","lives","health","timer","level"],\n'
    '    "mechanics": ["jump","gravity","collision","win_goal","timer","score_gain"],\n'
    '    "players": 1, "enemies": 3, "difficulty": 2\n'
    "  }\n"
)


def build_prompt(user_text: str) -> str:
    """Собирает итоговый промпт: system + жёсткая инструкция + текст игрока."""
    instruction = (
        "Turn the player's game idea below into one JSON object matching the "
        "schema. Pick the closest enum values. Respond with JSON only.\n\n"
        "Player idea: {text}\n\nJSON:"
    ).format(text=user_text.strip())
    return SYSTEM_PROMPT + "\n\n" + instruction


def extract_json(raw: str) -> dict:
    """Достаёт первый JSON-объект из ответа модели (устойчив к мусору)."""
    start = raw.find("{")
    end = raw.rfind("}") if raw.rfind("}") > start else -1
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Malformed JSON from model: %s" % exc) from exc
