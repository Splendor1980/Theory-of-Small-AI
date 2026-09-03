extends Node2D

# =====================================================================
# Автосгенерированный скелет игрового узла (Agent 1, Godot 4.x).
# Заполняется по GDD-манифесту. Места «HAND» — точки для доработки.
# =====================================================================
## GENRE: {genre}
## LEVEL : {level_type}
## MOVEMENT: {player_movement}

var score := 0
var lives := {lives}
var difficulty := {difficulty}

func _ready() -> void:
    _setup_world()
    _spawn_enemies({enemies})

func _process(delta: float) -> void:
    _handle_input()

func _handle_input() -> void:
    # HAND: привяжите физический ввод к игроку.
    pass

func _setup_world() -> void:
    # HAND: создайте пол/платформы/арену под {level_type}.
    pass

func _spawn_enemies(count: int) -> void:
    # HAND: расставьте {enemies} врагов со стилем «{enemy_behavior}».
    for i in count:
        pass

func _on_score_gain(amount: int) -> void:
    score += amount
    print("SCORE: %d" % score)

func _on_player_hit() -> void:
    lives -= 1
    if lives <= 0:
        _on_game_over()

func _on_game_over() -> void:
    print("GAME OVER")
    get_tree().quit()

## UI: {ui}
## MECHANICS: {mechanics}
