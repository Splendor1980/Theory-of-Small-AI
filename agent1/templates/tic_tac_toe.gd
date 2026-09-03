extends Control
# =====================================================================
# Крестики-нолики (Tic-Tac-Toe), Godot 4.x.
# Полностью играбельно: клик мышью по клетке, ИИ ходит крестиками-ноликами.
# Автосгенерировано библиотекой шаблонов Agent 1.
# =====================================================================
## GAME: tic_tac_toe

# ===================== THEME (настраивается) =====================
## THEME_START
# Меняется роутером/пользователем без правки механики.
const THEME_TITLE := "{{THEME_TITLE}}"
const THEME_MARK_X := "{{THEME_MARK_X}}"          # символ/метка игрока X
const THEME_MARK_O := "{{THEME_MARK_O}}"          # символ/метка игрока O
const THEME_COLOR_X := Color({{THEME_COLOR_X}})   # цвет метки X
const THEME_COLOR_O := Color({{THEME_COLOR_O}})   # цвет метки O
const THEME_COLOR_GRID := Color({{THEME_COLOR_GRID}})
const THEME_COLOR_WIN := Color({{THEME_COLOR_WIN}})
const THEME_BG := Color({{THEME_BG}})
## THEME_END
# =============================================================

var board := ["", "", "", "", "", "", "", "", ""]
var current := "X"
var game_over := false
var player_side := "X"
var ai_side := "O"
var win_lines := [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
]
var cell_size := 120.0
var origin := Vector2(40, 40)
var line_win: Array = []


func _ready() -> void:
    _reset()


func _reset() -> void:
    board = ["", "", "", "", "", "", "", "", ""]
    current = "X"
    game_over = false
    line_win = []
    queue_redraw()


func _process(_delta: float) -> void:
    if not game_over and current == ai_side:
        _ai_move.call_deferred()


func _gui_input(event: InputEvent) -> void:
    if game_over or current != player_side:
        return
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        var idx := _cell_at(event.position)
        if idx >= 0 and board[idx] == "":
            _place(idx, player_side)
            if not game_over:
                current = ai_side


func _place(idx: int, mark: String) -> void:
    board[idx] = mark
    queue_redraw()
    var w := _check_winner()
    if w["win"]:
        game_over = true
        line_win = w["line"]
    elif not board.has(""):
        game_over = true
    else:
        current = "X" if current == "O" else "O"


func _ai_move() -> void:
    var idx := _best_move(ai_side)
    if idx >= 0:
        _place(idx, ai_side)
        if not game_over:
            current = player_side


func _best_move(side: String) -> int:
    # 1) победа, 2) блок, 3) центр, 4) углы, 5) первое свободное
    var move := _find_winning(side)
    if move >= 0:
        return move
    var opponent := "X" if side == "O" else "O"
    move = _find_winning(opponent)
    if move >= 0:
        return move
    if board[4] == "":
        return 4
    for corner in [0, 2, 6, 8]:
        if board[corner] == "":
            return corner
    for i in range(9):
        if board[i] == "":
            return i
    return -1


func _find_winning(side: String) -> int:
    for line in win_lines:
        var spots := 0
        var empty := -1
        for idx in line:
            if board[idx] == side:
                spots += 1
            elif board[idx] == "":
                empty = idx
        if spots == 2 and empty >= 0:
            return empty
    return -1


func _check_winner() -> Dictionary:
    for line in win_lines:
        if board[line[0]] != "" and board[line[0]] == board[line[1]] and board[line[1]] == board[line[2]]:
            return {"win": true, "line": line}
    return {"win": false, "line": []}


func _cell_at(pos: Vector2) -> int:
    for i in range(9):
        var row := i / 3
        var col := i % 3
        var rect := Rect2(origin + Vector2(col, row) * cell_size, Vector2(cell_size, cell_size))
        if rect.has_point(pos):
            return i
    return -1


func _draw() -> void:
    var bg := Rect2(Vector2.ZERO, get_viewport_rect().size)
    draw_rect(bg, THEME_BG)
    var board_w := cell_size * 3.0
    for i in range(1, 3):
        var p1 := origin + Vector2(i * cell_size, 0)
        var p2 := origin + Vector2(i * cell_size, board_w)
        draw_line(p1, p2, THEME_COLOR_GRID, 3.0)
        var p3 := origin + Vector2(0, i * cell_size)
        var p4 := origin + Vector2(board_w, i * cell_size)
        draw_line(p3, p4, THEME_COLOR_GRID, 3.0)
    for i in range(9):
        var row := i / 3
        var col := i % 3
        var center := origin + Vector2((col + 0.5) * cell_size, (row + 0.5) * cell_size)
        if board[i] == "X":
            draw_line(center + Vector2(-30, -30), center + Vector2(30, 30), THEME_COLOR_X, 6.0)
            draw_line(center + Vector2(30, -30), center + Vector2(-30, 30), THEME_COLOR_X, 6.0)
        elif board[i] == "O":
            draw_arc(center, 30.0, 0, TAU, 32, THEME_COLOR_O, 6.0)
    if not line_win.is_empty():
        var a := origin + Vector2((line_win[0] % 3 + 0.5) * cell_size, (line_win[0] / 3 + 0.5) * cell_size)
        var b := origin + Vector2((line_win[2] % 3 + 0.5) * cell_size, (line_win[2] / 3 + 0.5) * cell_size)
        draw_line(a, b, THEME_COLOR_WIN, 8.0)
