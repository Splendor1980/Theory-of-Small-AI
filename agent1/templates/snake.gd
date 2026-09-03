extends Node2D
# =====================================================================
# Змейка (Snake), Godot 4.x.
# Играбельный MVP: змейка, стрелки/WASD, еда, рост, очки, game over.
# Автосгенерировано библиотекой шаблонов Agent 1.
# =====================================================================
## GAME: snake

# ===================== THEME (настраивается) =====================
## THEME_START
# Меняется роутером/пользователем без правки механики.
const THEME_TITLE := "{{THEME_TITLE}}"
const THEME_COLOR_SNAKE := Color({{THEME_COLOR_SNAKE}})
const THEME_COLOR_SNAKE_HEAD := Color({{THEME_COLOR_SNAKE_HEAD}})
const THEME_COLOR_FOOD := Color({{THEME_COLOR_FOOD}})
const THEME_COLOR_GRID := Color({{THEME_COLOR_GRID}})
const THEME_BG := Color({{THEME_BG}})
## THEME_END
# =============================================================

var grid_w := 30
var grid_h := 20
var cell := 24.0
var snake: Array = []          # [{Vector2}] голова впереди
var dir := Vector2.RIGHT
var next_dir := Vector2.RIGHT
var food := Vector2.ZERO
var score := 0
var game_over := false
var rng := RandomNumberGenerator.new()
var tick_acc := 0.0
var tick_interval := 0.16


func _ready() -> void:
    _reset()


func _reset() -> void:
    snake = [Vector2(5, grid_h / 2), Vector2(4, grid_h / 2), Vector2(3, grid_h / 2)]
    dir = Vector2.RIGHT
    next_dir = Vector2.RIGHT
    score = 0
    game_over = false
    tick_acc = 0.0
    _place_food()


func _place_food() -> void:
    while true:
        food = Vector2(rng.randi_range(0, grid_w - 1), rng.randi_range(0, grid_h - 1))
        if not snake.has(food):
            break


func _process(delta: float) -> void:
    if game_over:
        return
    _handle_input()
    tick_acc += delta
    if tick_acc >= tick_interval:
        tick_acc -= tick_interval
        _tick()
    queue_redraw()


func _handle_input() -> void:
    if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W):
        if dir != Vector2.DOWN:
            next_dir = Vector2.UP
    elif Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
        if dir != Vector2.UP:
            next_dir = Vector2.DOWN
    elif Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A):
        if dir != Vector2.RIGHT:
            next_dir = Vector2.LEFT
    elif Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
        if dir != Vector2.LEFT:
            next_dir = Vector2.RIGHT


func _tick() -> void:
    dir = next_dir
    var head := snake[0] + dir
    # стены
    if head.x < 0 or head.x >= grid_w or head.y < 0 or head.y >= grid_h:
        game_over = true
        return
    # самопересечение (кроме хвоста, который сместится)
    if snake.has(head) and head != snake[-1]:
        game_over = true
        return
    snake.push_front(head)
    if head == food:
        score += 1
        _place_food()
    else:
        snake.pop_back()


func _draw() -> void:
    var sz := Vector2(grid_w * cell, grid_h * cell)
    draw_rect(Rect2(Vector2.ZERO, sz), THEME_BG)
    # сетка (лёгкая)
    for x in range(1, grid_w):
        draw_line(Vector2(x * cell, 0), Vector2(x * cell, grid_h * cell), THEME_COLOR_GRID, 1.0)
    for y in range(1, grid_h):
        draw_line(Vector2(0, y * cell), Vector2(grid_w * cell, y * cell), THEME_COLOR_GRID, 1.0)
    # еда
    draw_rect(Rect2(food * cell + Vector2(2, 2), Vector2(cell - 4, cell - 4)), THEME_COLOR_FOOD)
    # змейка
    for i in range(snake.size()):
        var c := THEME_COLOR_SNAKE if i > 0 else THEME_COLOR_SNAKE_HEAD
        draw_rect(Rect2(snake[i] * cell + Vector2(1, 1), Vector2(cell - 2, cell - 2)), c)
    # счёт
    var face := ThemeDB.fallback_font
    draw_string(face, Vector2(8, 24), "%s — очки: %d" % [THEME_TITLE, score],
                HORIZONTAL_ALIGNMENT_LEFT, sz.x, 22, THEME_COLOR_SNAKE_HEAD)
    if game_over:
        draw_string(face, Vector2(30, sz.y / 2.0), "ИГРА КОНЧЕНА — очки: %d" % score,
                    HORIZONTAL_ALIGNMENT_LEFT, sz.x - 60, 36, THEME_COLOR_FOOD)
