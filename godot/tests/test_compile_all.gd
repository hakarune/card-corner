extends SceneTree
## Compile gate. `--editor --quit` builds the class cache + reimports but
## does NOT resolve autoload identifiers in plain scripts or deep-parse
## scripts a scene only references -- that gap let a `:=`-on-Dictionary
## slip through once. This walks res://, load()s every .gd (forces a full
## compile) and instantiate()s every .tscn, run deferred so autoloads are
## live (a SceneTree run loads them like the real game does).


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var scripts: Array[String] = []
	var scenes: Array[String] = []
	_walk("res://", scripts, scenes)

	var failures: Array[String] = []
	for path in scripts:
		if path == "res://tests/test_compile_all.gd":
			continue
		var res := load(path)
		if res == null:
			failures.append(path + "  (script failed to compile)")
	for path in scenes:
		var ps := load(path) as PackedScene
		if ps == null:
			failures.append(path + "  (scene failed to load)")
			continue
		var inst := ps.instantiate()
		if inst == null:
			failures.append(path + "  (scene failed to instantiate)")
		else:
			inst.free()

	print("== compile_all: %d scripts + %d scenes checked, %d failed ==" %
		[scripts.size(), scenes.size(), failures.size()])
	for f in failures:
		printerr("  FAIL ", f)
	quit(1 if failures.size() > 0 else 0)


func _walk(dir_path: String, scripts: Array[String], scenes: Array[String]) -> void:
	var d := DirAccess.open(dir_path)
	if d == null:
		return
	d.list_dir_begin()
	var entry := d.get_next()
	while entry != "":
		if entry.begins_with("."):
			entry = d.get_next()
			continue
		var full := dir_path.path_join(entry)
		if d.current_is_dir():
			_walk(full, scripts, scenes)
		elif full.ends_with(".gd"):
			scripts.append(full)
		elif full.ends_with(".tscn"):
			scenes.append(full)
		entry = d.get_next()
	d.list_dir_end()
