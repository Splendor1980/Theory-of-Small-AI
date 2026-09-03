extends Node2D
# =====================================================================
# Пинг-понг (Pong), Godot 4.x.
# Играбельный MVP: ракетки, мяч, ИИ-соперник, очки, победа.
# Автосгенерировано библиотекой шаблонов Agent 1.
# =====================================================================
## GAME: pong

# ===================== THEME (настраивается) =====================
## THEME_START
# Меняется роутером/пользователем без правки механики.
const THEME_TITLE := "{{THEME_TITLE}}"
const THEME_COLOR_PADDLE_L := Color({{THEME_COLOR_PADDLE_L}})
const THEME_COLOR_PADDLE_R := Color({{THEME_COLOR_PADDLE_R}})
const THEME_COLOR_BALL := Color({{THEME_COLOR_BALL}})
const THEME_COLOR_NET := Color({{THEME_COLOR_NET}})
const THEME_BG := Color({{THEME_BG}})
## THEME_END
# =============================================================

var screen := Vector2(1280, 720)
var paddle_w := 14.0
var paddle_h := 110.0
var pad_l_y := 0.0
var pad_r_y := 0.0
var ball := Vector2(0, 0)
var ball_v := Vector2(0, 0)
var ball_speed := 420.0
var score_l := 0
var score_r := 0
var win_target := 5
var game_over := false
var rng := RandomNumberGenerator.new()


func _ready() -> void:
    _reset()


func _reset() -> void:
    pad_l_y = (screen.y - paddle_h) / 2.0
    pad_r_y = (screen.y - paddle_h) / 2.0
    score_l = 0
    score_r = 0
    game_over = false
    _center_ball()


func _center_ball() -> void:
    ball = screen / 2.0
    ball_v = Vector2((1 if rng.randf() < 0.5 else -1) * ball_speed, (rng.randf() - 0.5) * 2.0 * ball_speed).normalized() * ball_speed


func _process(delta: float) -> void:
    if game_over:
        return
    _move_player(delta)
    _move_ai(delta)
    _move_ball(delta)
    queue_redraw()


func _move_player(delta: float) -> void:
    var up := Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)
    var down := Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN)
    var mv := 0.0
    if up:
        mv -= 1.0
    if down:
        mv += 1.0
    pad_l_y = clampf(pad_l_y + mv * 520.0 * delta, 0.0, screen.y - paddle_h)


func _move_ai(delta: float) -> void:
    var target := ball.y - paddle_h / 2.0
    var diff := target - pad_r_y
    var mv := clampf(diff, -1.0, 1.0) * 430.0 * delta
    pad_r_y = clampf(pad_r_y + mv, 0.0, screen.y - paddle_h)


func _move_ball(delta: float) -> void:
    ball += ball_v * delta
    # верх/низ
    if ball.y < 0.0:
        ball.y = 0.0
        ball_v.y = -ball_v.y
    elif ball.y > screen.y:
        ball.y = screen.y
        ball_v.y = -ball_v.y
    # ракетки
    _v_paddle(pad_l_y, true)
    _v_paddle(pad_r_y, false)
    # голы
    if ball.x < -30.0:
        score_r += 1
        _check_win()
        _center_ball()
    elif ball.x > screen.x + 30.0:
        score_l += 1
        _check_win()
        _center_ball()


func _v_paddle(py: float, is_left: bool) -> void:
    var px := ( paddle_w if is_left else screen.x - paddle_w )
    if ball.x > px - 16.0 and ball.x < px + 16.0:
        if ball.y > py - 6.0 and ball.y < py + paddle_h + 6.0:
            if (is_left and ball_v.x < 0 and ball.x > px) or (not is_left and ball_v.x > 0 and ball.x < px):
                ball_v.x = -ball_v.x
                ball_v.x = signf(ball_v.x) * maxf(ball_speed, absf(ball_v.x) * 1.05)
                ball_v.y += (ball.y - (py + paddle_h / 2.0)) / (paddle_h / 2.0) * 160.0
                ball_v = ball_v.normalized() * ball_speed


func _check_win() -> void:
    if score_l >= win_target or score_r >= win_target:
        game_over = true


func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, screen), THEME_BG)
    # сетка
    draw_line(Vector2(screen.x / 2.0, 0), Vector2(screen.x / 2.0, screen.y), THEME_COLOR_NET, 2.0)
    # ракетки
    draw_rect(Rect2(Vector2(0, pad_l_y), Vector2(paddle_w, paddle_h)), THEME_COLOR_PADDLE_L)
    draw_rect(Rect2(Vector2(screen.x - paddle_w, pad_r_y), Vector2(paddle_w, paddle_h)), THEME_COLOR_PADDLE_R)
    # мяч
    draw_circle(ball, 9.0, THEME_COLOR_BALL)
    # счёт
    var face := ThemeDB.fallback_font
    draw_string(face, Vector2(screen.x / 2.0 - 60, 50), "%d" % score_l, HORIZONTAL_ALIGNMENT_LEFT, 120.0, 48, THEME_COLOR_PADDLE_L)
    draw_string(face, Vector2(screen.x / 2.0 + 20, 50), "%d" % score_r, HORIZONTAL_ALIGNMENT_LEFT, 120.0, 48, THEME_COLOR_PADDLE_R)
    if game_over:
        var w := "ИГРА КОНЧЕНА: %s" % ("ЛЕВЫЙ" if score_l > score_r else "ПРАВЫЙ")
        draw_string(face, Vector2(screen.x / 2.0 - 260, screen.y / 2.0), w, HORIZONTAL_ALIGNMENT_LEFT, 520.0, 40, THEME_COLOR_BALL)
