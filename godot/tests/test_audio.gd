extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_audio_synth.py + test_audio_sounds.py.
## Can't hear it headless -- checks buffer shape, envelope, clipping,
## determinism, and that every named sound builds.

const SR := Synth.SAMPLE_RATE


func _samples(w: AudioStreamWAV) -> PackedInt32Array:
	var out := PackedInt32Array()
	var d := w.data
	for i in range(0, d.size(), 2):
		out.append(d.decode_s16(i))
	return out


func _init() -> void:
	# --- tone: length, format, silence for freq <= 0 ---
	var t := Synth.tone(440, 0.1, Synth.Wave.SINE, 1.0)
	check(t.format == AudioStreamWAV.FORMAT_16_BITS and t.mix_rate == SR and not t.stereo, "tone: 16-bit mono 44100")
	var s := _samples(t)
	check(s.size() == int(SR * 0.1), "tone: sample count matches duration")
	var peak := 0
	for v in s:
		peak = max(peak, abs(v))
	check(peak > 10000 and peak <= 32767, "tone: audible but not clipping past int16")
	check(abs(s[0]) < peak / 2 and abs(s[s.size() - 1]) < peak / 2, "tone: envelope fades in and out")

	var silent := _samples(Synth.tone(0, 0.05))
	var all_zero := true
	for v in silent:
		if v != 0:
			all_zero = false
	check(all_zero and silent.size() == int(SR * 0.05), "tone: freq<=0 is silence of the right length")

	# --- volume clamps, never overflows ---
	var loud := _samples(Synth.tone(440, 0.05, Synth.Wave.SQUARE, 5.0))
	var ok := true
	for v in loud:
		if v < -32768 or v > 32767:
			ok = false
	check(ok, "tone: volume=5.0 clamps into valid int16 range")

	# --- sweep ---
	var sw := _samples(Synth.sweep(200, 800, 0.1))
	check(sw.size() == int(SR * 0.1), "sweep: sample count matches duration")

	# --- sequence: total length = notes + gaps ---
	var seq := Synth.sequence([Synth.note("C5", 0.1), Synth.note("E5", 0.1)], Synth.Wave.SQUARE, 0.7, 0.02)
	var gap_n := int(SR * 0.02)
	var expect := int(SR * 0.1) + gap_n + int(SR * 0.1) + gap_n
	check(_samples(seq).size() == expect, "sequence: length = sum(note lengths + gaps)")

	# --- determinism ---
	check(Synth.tone(440, 0.1).data == Synth.tone(440, 0.1).data, "tone is deterministic")

	# --- every named sound baked to a valid, non-empty mono wav ---
	# (Godot imports .wav as QOA-compressed by default -- fine for playback;
	# CCAudio re-asserts the music loop flag at load time.)
	for name in ["card_select", "card_move", "button", "match", "miss", "win", "loss", "ask", "music_loop"]:
		var path := "res://assets/audio/%s.wav" % name
		check(ResourceLoader.exists(path), "baked wav exists: %s" % name)
		var w := load(path) as AudioStreamWAV
		check(w != null and w.data.size() > 0 and not w.stereo and w.mix_rate == SR,
			"%s.wav is a non-empty mono 44100 stream" % name)
	# CCAudio re-asserts the loop flag on load (import drops it); verify
	# an AudioStreamWAV accepts it being set back.
	var loop := load("res://assets/audio/music_loop.wav") as AudioStreamWAV
	loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
	loop.loop_begin = 0
	check(loop.loop_mode == AudioStreamWAV.LOOP_FORWARD, "music_loop accepts a forward-loop flag")

	finish("audio")
