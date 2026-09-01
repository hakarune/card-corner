class_name GameScreen
extends Control
## Base for a full-window game screen. Analogue of legacy/ui/screen.py.
## Scene routing (menu / pause / quit) is wired in Phase 6; for now a
## screen emits these and a host (or standalone run) decides what to do.

signal go_to_menu
signal restart_requested
signal quit_app


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
