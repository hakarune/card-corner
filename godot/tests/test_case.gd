extends SceneTree
## Minimal headless test base. A concrete test `extends` this and does its
## work in `_init()`, calling `check()` / `check_eq()` and finishing with
## `finish("Title")`. Run: godot --headless --path godot --script res://tests/test_<x>.gd
## (ERROR lines printed by intentional push_error() paths under test are expected.)

var _failures := 0
var _count := 0


func check(cond: bool, msg: String) -> void:
	_count += 1
	if cond:
		print("  ok   ", msg)
	else:
		_failures += 1
		printerr("  FAIL ", msg)


func check_eq(actual, expected, msg: String) -> void:
	check(_deep_eq(actual, expected), "%s  (got %s, expected %s)" % [msg, actual, expected])


func _deep_eq(a, b) -> bool:
	if typeof(a) != typeof(b):
		return a == b
	if a is Array:
		if a.size() != b.size():
			return false
		for i in a.size():
			if not _deep_eq(a[i], b[i]):
				return false
		return true
	return a == b


func finish(title: String) -> void:
	var passed := _count - _failures
	print("== %s: %d/%d passed ==" % [title, passed, _count])
	quit(1 if _failures > 0 else 0)
