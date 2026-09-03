extends Node2D
# =====================================================================
# Хост-точка входа агента: подгружает выбранную игру из res://games/.
# Выбор игры: константа GAME_NAME (правится make_project.py) или
# переменная окружения GAME_NAME. Игры — это обычные Node2D-скрипты
# (templates/*.gd, скопированные в games/).
# =====================================================================
## GAME_HOST

const GAME_NAME := "GAME_NAME_PLACEHOLDER"

var _game: Node2D


func _ready() -> void:
    var name2 := GAME_NAME
    if name2 == "GAME_NAME_PLACEHOLDER":
        name2 = OS.get_environment("GAME_NAME")
    if name2 == "":
        name2 = "tic_tac_toe"
    _spawn(name2)


func _spawn(game_name: String) -> void:
    var path := "res://games/%s.gd" % game_name
    if not ResourceLoader.exists(path):
        print("ERR: no game script at ", path)
        get_tree().quit(1)
        return
    var script := load(path)
    var node := Node2D.new()
    node.name = "Game_" + game_name
    node.set_script(script)
    add_child(node)
