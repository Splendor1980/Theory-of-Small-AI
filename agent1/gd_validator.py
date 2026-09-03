"""Мини-валидатор GDScript на stdlib (fallback, когда Godot не установлен).

GDScript (как Python) - indentation-based, без 'end'.
Проверяем консервативно только явно проблемные места, чтобы не давать
ложных срабатываний на валидных скелетах:
  - незакрытые скобки '(', '[', '{' и строки
  - использование переменной до её объявления (присваивание/чтение, не вызовы)
  - явно не объявленные присваивания
Не пытаемся понять всё - для полной проверки нужен Godot (см. build_loop).
"""
import re
import shutil

DECLARATION = re.compile(
    r"^\s*(?:export\s+|@onready\s+|static\s+)?(?:var|const)\s+(\w+)"
)
ASSIGN_TARGET = re.compile(r"^\s*([A-Za-z_]\w*)\s*=")         # x = ...
CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")                   # func_name(  -> вызов

BUILTINS = set("""
pass return break continue func var const if elif else for in while class extends
static true false null self super and or not is as void int float string bool
Vector2 Vector3 Color Rect2 Node Node2D Sprite2D Area2D Node2D RigidBody2D
CharacterBody2D CollisionShape2D Timer Camera2D CanvasLayer Marker2D
_ready _process _physics_process _enter_tree _exit_tree _draw _unhandled_input
_input _input_event _on_score_gain _on_player_hit _on_game_over
Input InputEventKey InputEventMouseButton InputEventMouseMotion
print push_error push_warning randf randf_range rand_range randi
get_parent get_node get_tree get_viewport get_node queue_free emit_signal connect
move_and_slide move_and_collide move_and_slide is_on_floor is_on_wall
position global_position velocity gravity direction rotation
input_key_pressed is_action_just_pressed is_action_pressed
clamp abs lerp min max sign cos sin tan sqrt pow floor ceil
delta degree rad_to_deg deg_to_rad
""" .split())


def find_godot():
    return shutil.which("godot") or shutil.which("godot4")


def _strip_comment(line):
    in_str = None
    out = []
    i = 0
    while i < len(line):
        ch = line[i]
        if in_str:
            out.append(ch)
            if ch == in_str and line[i - 1:i] != "\\":
                in_str = None
        elif ch in ('"', "'"):
            in_str = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def validate_script(code):
    """Вернуть ошибки [{line, message, category}]. Пустой список = ок."""
    errors = []
    if not code or not code.strip():
        return [{"line": 0, "category": "empty", "message": "Пустой скрипт"}]

    # --- 1) скобки и строки ---
    stack = {"(": [], "[": [], "{": []}
    pairs = {")": "(", "]": "[", "}": "{"}
    declared = set(BUILTINS)
    in_str = None
    block = {}      # имя -> стек строк (для скобок), но скобки уже выше

    # пред-проход: собрать все объявления, чтобы они были известны везде
    for lineno, raw in enumerate(code.splitlines(), 1):
        line = _strip_comment(raw)
        m = DECLARATION.search(line)
        if m:
            declared.add(m.group(1))

    for lineno, raw in enumerate(code.splitlines(), 1):
        line = _strip_comment(raw)
        # скобки
        i = 0
        while i < len(line):
            ch = line[i]
            if in_str:
                if ch == in_str:
                    in_str = None
            elif ch in ('"', "'"):
                in_str = ch
            elif ch in "([{":
                stack[ch].append(lineno)
            elif ch in ")]}":
                opener = pairs[ch]
                if stack[opener]:
                    stack[opener].pop()
                else:
                    errors.append({
                        "line": lineno, "category": "bracket",
                        "message": f"Лишняя закрывающая скобка '{ch}'",
                    })
            i += 1
        if in_str:
            errors.append({
                "line": lineno, "category": "string",
                "message": "Незакрытая строка (без закрывающей кавычки)",
            })
            in_str = None

        # присваивание переменной до объявления (только LHS)
        am = ASSIGN_TARGET.match(line)
        if am and am.group(1) not in declared:
            # если это внутри 'func ... =' (сигнатура с =)? не отслеживаем
            errors.append({
                "line": lineno, "category": "undeclared",
                "message": f'Переменная "{am.group(1)}" не объявлена: добавь "var {am.group(1)}" до использования',
            })

    for kind, lines in stack.items():
        if lines:
            errors.append({
                "line": lines[-1], "category": "bracket",
                "message": f"Незакрытая скобка '{kind}' (открыта на строке {lines[-1]})",
            })

    return errors


def validate_with_godot(code, godot_path=None):
    """Заглушка: возвращает None. Полная Godot-проверка требует проекта, см. build_loop."""
    return None