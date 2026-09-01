extends SceneTree
## Dev tool: synthesize every game sound (Synth, ported from the legacy
## Python synth) and write it to res://assets/audio/<name>.wav, which
## CCAudio loads at runtime (GDScript per-sample synthesis is too slow to
## run at load time). Re-run after changing synth.gd or a sound recipe:
##   godot --headless --path godot --script res://tools/bake_audio.gd

const OUT_DIR := "res://assets/audio"


func _init() -> void:
	var S := Synth
	var recipes := {
		"card_select": func(): return S.tone(880, 0.05, S.Wave.SINE, 0.6),
		"card_move": func(): return S.sweep(700, 320, 0.14, S.Wave.TRIANGLE, 0.5),
		"button": func(): return S.tone(700, 0.04, S.Wave.SINE, 0.45),
		"match": func(): return S.sequence([S.note("C5", 0.08), S.note("E5", 0.08), S.note("G5", 0.16)], S.Wave.SQUARE, 0.7),
		"miss": func(): return S.sequence([S.note("A4", 0.12), S.note("F4", 0.18)], S.Wave.SINE, 0.5),
		"win": func(): return S.sequence([S.note("C5", 0.1), S.note("E5", 0.1), S.note("G5", 0.1), S.note("C6", 0.3)], S.Wave.SQUARE, 0.75),
		"loss": func(): return S.sequence([S.note("E4", 0.18), S.note("C4", 0.3)], S.Wave.SINE, 0.55),
		"ask": func(): return S.sequence([S.note("E5", 0.07), S.note("A5", 0.1)], S.Wave.TRIANGLE, 0.55),
		"music_loop": func():
			var melody := [
				S.note("C5", 0.3), S.note("E5", 0.3), S.note("G5", 0.3), S.note("E5", 0.3),
				S.note("C5", 0.3), S.note("D5", 0.3), S.note("E5", 0.3), S.note("G5", 0.5),
				S.note("F5", 0.3), S.note("E5", 0.3), S.note("D5", 0.3), S.note("C5", 0.5),
			]
			# The forward loop is applied at import time
			# (assets/audio/music_loop.wav.import: edit/loop_mode=2).
			return S.sequence(melody, S.Wave.SQUARE, 0.35, 0.01),
	}

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var d := DirAccess.open("res://assets")
	if d and not d.dir_exists("audio"):
		d.make_dir("audio")

	for name in recipes:
		var w: AudioStreamWAV = recipes[name].call()
		var path := "%s/%s.wav" % [OUT_DIR, name]
		var err := w.save_to_wav(path)
		print("  %s  -> %s  (%d samples, err %d)" % [name, path, w.data.size() / 2, err])
	print("baked %d sounds" % recipes.size())
	quit()
