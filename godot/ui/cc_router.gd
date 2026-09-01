extends Node
## Autoload: screen routing + config hand-off. Analogue of legacy main.py's
## screen stack. A screen calls CCRouter.consume() in _ready() to pick up
## whatever config the previous screen passed (empty dict when a scene is
## run standalone).

const SCENES := {
	"menu": "res://ui/main_menu.tscn",
	"difficulty": "res://ui/difficulty_select.tscn",
	"go_fish": "res://games/go_fish/go_fish.tscn",
	"old_maid": "res://games/old_maid/old_maid.tscn",
	"memory": "res://games/memory/memory.tscn",
	"letter_match": "res://games/letter_match/letter_match.tscn",
}

var _pending := {}


func goto_menu() -> void:
	_pending = {}
	_change("menu")


## `game` is one of the SCENES keys ("go_fish" etc.) or "letter_match".
func goto_difficulty(game: String) -> void:
	_pending = {"game": game}
	_change("difficulty")


## `cfg` e.g. {"difficulty": AIStrategy.Difficulty.EASY} or {"solo": true}
## or {"mode": "animals"}.
func goto_game(game_key: String, cfg: Dictionary = {}) -> void:
	_pending = cfg
	_change(game_key)


func consume() -> Dictionary:
	var p := _pending
	_pending = {}
	return p


func _change(key: String) -> void:
	get_tree().change_scene_to_file(SCENES[key])
