"""Схема файла описания игры (GDD-lite).

Tiny LLM не генерирует полные игры — он генерирует компактный JSON-манифест
(сцену/механику), который мы затем уверенно мапим на GDScript-шаблоны.

Требования к схеме:
  - плоская и короткая (модель 527k не осилит вложенность);
  - каждый ключ имеет ограниченный набор значений (enum/protected vocabulary),
    чтобы уменьшить галлюцинации;
  - неизвестные ключи игнорируются парсером (lenient parse).
"""


# --- Ограниченные словари (protected vocabulary) ---
GENRES = {"platformer", "puzzle", "runner", "twin_stick", "clicker", "top_down"}

PLAYER_MOVEMENT = {"left_right", "left_right_jump", "free_2d", "static"}
PLAYER_SHOOT = {"none", "bullet", "auto_aim"}

ENEMY_BEHAVIOR = {"patrol", "chase", "static", "shoot"}
ENEMY_KIND = {"walker", "flyer", "turret", "boss"}

LEVEL_TYPE = {"side_scroll", "top_down", "fixed_arena", "vertical"}
COLOR_SCHEME = {"retro", "neon", "pastel", "mono"}

UI_ELEMENTS = {"score", "lives", "health", "timer", "level"}

MECHANICS = {"jump", "gravity", "collision", "win_goal", "timer", "score_gain"}


class GameIntent(dict):
    """Представление намерения игрока в нормализованном виде.

    dict-подкласс: легко сериализуется и легко превращается в GDScript.
    Неизвестные поля отбрасываются, значения приводятся к валидному виду.
    """

    VALID = {
        "genre": GENRES,
        "player_movement": PLAYER_MOVEMENT,
        "player_shoot": PLAYER_SHOOT,
        "enemy_behavior": ENEMY_BEHAVIOR,
        "enemy_kind": ENEMY_KIND,
        "level_type": LEVEL_TYPE,
        "color_scheme": COLOR_SCHEME,
        "ui": UI_ELEMENTS,          # set
        "mechanics": MECHANICS,     # set
        "players": int,             # 1..4
        "enemies": int,             # 0..50
        "difficulty": int,          # 1..5
    }

    @classmethod
    def from_dict(cls, raw: dict) -> "GameIntent":
        obj = cls()
        for key, guard in cls.VALID.items():
            if key not in raw:
                continue
            if key in ("ui", "mechanics"):
                allowed = {s.lower() for s in guard}
                obj[key] = {s.lower() for s in raw[key]
                            if isinstance(s, str) and s.lower() in allowed}
            elif isinstance(guard, set):
                val = raw[key]
                if isinstance(val, str) and val.lower() in guard:
                    obj[key] = val.lower()
            elif isinstance(guard, type) and isinstance(raw[key], guard):
                obj[key] = max(guard(raw[key]), 0)
        return obj

    @property
    def is_valid(self) -> bool:
        return "genre" in self and "level_type" in self
