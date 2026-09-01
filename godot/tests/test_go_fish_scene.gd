extends SceneTree
## Headless smoke test for the Go Fish SCREEN: instantiate the scene, drive
## it to completion by simulating human card taps + hand-overs, assert it
## terminates with no script errors. Deferred + await process_frame so the
## tree (and autoloads) run normally.


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	Engine.time_scale = 80.0  # drain the screen's real-time AI delays fast

	var packed: PackedScene = load("res://games/go_fish/go_fish.tscn")
	if packed == null:
		printerr("  FAIL could not load go_fish.tscn")
		_done(false)
		return
	var screen: Node = packed.instantiate()
	screen.difficulty = AIStrategy.Difficulty.MEDIUM
	root.add_child(screen)
	await process_frame
	await process_frame

	var taps := 0
	var start_ms := Time.get_ticks_msec()
	while true:
		await process_frame
		var g = screen._game
		if g == null:
			continue
		if g.game_over:
			print("  ok   Go Fish scene ran to game over (%d taps, winner='%s')" % [taps, g.winner])
			_done(true)
			return

		if screen._awaiting_handover:
			for v in screen._hand_views:
				if is_instance_valid(v) and v.card.rank == screen._pending_ai_ask:
					screen._on_card_clicked(v)
					break
		else:
			var idle: bool = (not screen._waiting_for_ai and screen._ai_resolve_timer <= 0.0
				and not screen._waiting_for_human_resolve)
			if idle and not g.is_ai_turn() and screen._hand_views.size() > 0:
				screen._on_card_clicked(screen._hand_views[0])
				taps += 1

		if taps > 3000 or (Time.get_ticks_msec() - start_ms) > 90000:
			printerr("  FAIL Go Fish scene did not terminate (taps=%d)" % taps)
			_done(false)
			return


func _done(ok: bool) -> void:
	print("== go_fish_scene: %d/1 passed ==" % (1 if ok else 0))
	quit(0 if ok else 1)
