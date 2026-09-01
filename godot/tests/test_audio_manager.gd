extends SceneTree
## Ported from legacy/tests/unit/test_audio_manager.py -- CCAudio's own
## behaviour (mute short-circuit, music idempotency, restart, round-robin,
## safe unknown-name). Deferred so the autoload is live.

var _fails := 0


func _init() -> void:
	_run.call_deferred()


func _ok(cond: bool, msg: String) -> void:
	if cond:
		print("  ok   ", msg)
	else:
		_fails += 1
		printerr("  FAIL ", msg)


func _run() -> void:
	var a := root.get_node("CCAudio")
	_ok(a != null, "CCAudio autoload present")
	a.set_muted(false)

	# --- sound resolution ---
	_ok(a._sound("card_move") is AudioStreamWAV, "resolves a known sfx to an AudioStreamWAV")
	_ok(a._build("bogus") == null, "unknown sound name -> null (no crash)")
	a.play_sfx("bogus")  # must not raise
	_ok(true, "play_sfx('bogus') is a safe no-op")

	# --- round-robin over the SFX voice pool ---
	a._sfx_idx = 0
	a.play_sfx("card_select")
	a.play_sfx("card_select")
	_ok(a._sfx_idx == 2, "each play_sfx advances the voice index")
	for _i in a.SFX_VOICES:
		a.play_sfx("button")
	_ok(a._sfx_idx == 2, "voice index wraps around the pool")

	# --- mute short-circuits SFX (index does not advance) ---
	a.set_muted(true)
	var idx_before: int = a._sfx_idx
	a.play_sfx("match")
	_ok(a.muted and a._sfx_idx == idx_before, "muted: play_sfx is a no-op")
	_ok(not a._music.playing, "muted: music is stopped")

	# --- unmute restarts music ---
	a.set_muted(false)
	a.start_music()
	_ok(not a.muted and a._music.stream != null, "unmute + start_music assigns the loop stream")
	_ok(a._music.stream.loop_mode == AudioStreamWAV.LOOP_FORWARD, "music stream is a forward loop (import-baked)")

	# --- start_music is idempotent about the stream it uses ---
	var s1 = a._music.stream
	a.start_music()
	_ok(a._music.stream == s1, "start_music reuses the cached loop stream")

	print("== audio_manager: %d failure(s) ==" % _fails)
	quit(1 if _fails > 0 else 0)
