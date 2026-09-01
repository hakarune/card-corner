extends Node
## Autoload: SFX + background music, all procedurally synthesized (Synth).
## Ported from legacy/audio/{sounds,manager}.py. Sounds are built lazily on
## first use and cached, so a headless run that never plays audio pays
## nothing.

const SFX_VOICES := 6

var muted := false
var sfx_volume := 0.9
var music_volume := 0.45

var _bank := {}
var _sfx_players: Array[AudioStreamPlayer] = []
var _sfx_idx := 0
var _music: AudioStreamPlayer


func _ready() -> void:
	for _i in SFX_VOICES:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_sfx_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Master"
	add_child(_music)


func play_sfx(key: String) -> void:
	if muted:
		return
	var stream := _sound(key)
	if stream == null:
		return
	var p := _sfx_players[_sfx_idx]
	_sfx_idx = (_sfx_idx + 1) % _sfx_players.size()
	p.stream = stream
	p.volume_db = linear_to_db(sfx_volume)
	p.play()


func start_music() -> void:
	if _music.playing or muted:
		return
	var stream := _sound("music_loop")
	if stream == null:
		return
	_music.stream = stream
	_music.volume_db = linear_to_db(music_volume)
	_music.play()


func stop_music() -> void:
	_music.stop()


func set_muted(value: bool) -> void:
	muted = value
	if muted:
		_music.stop()
		for p in _sfx_players:
			p.stop()
	else:
		start_music()


func _sound(key: String) -> AudioStreamWAV:
	if not _bank.has(key):
		# Prefer a pre-baked .wav (tools/bake_audio.gd) -- GDScript
		# per-sample synth is too slow to run at load time. Fall back to
		# live synthesis if the baked file is missing.
		var baked := "res://assets/audio/%s.wav" % key
		if ResourceLoader.exists(baked):
			# music_loop.wav.import sets edit/loop_mode=2 (Forward), so the
			# loop is baked into the imported resource -- no runtime fix-up.
			_bank[key] = load(baked)
		else:
			_bank[key] = _build(key)
	return _bank[key]


func _build(key: String) -> AudioStreamWAV:
	var S := Synth
	match key:
		"card_select":
			return S.tone(880, 0.05, S.Wave.SINE, 0.6)
		"card_move":
			return S.sweep(700, 320, 0.14, S.Wave.TRIANGLE, 0.5)
		"button":
			return S.tone(700, 0.04, S.Wave.SINE, 0.45)
		"match":
			return S.sequence([S.note("C5", 0.08), S.note("E5", 0.08), S.note("G5", 0.16)], S.Wave.SQUARE, 0.7)
		"miss":
			return S.sequence([S.note("A4", 0.12), S.note("F4", 0.18)], S.Wave.SINE, 0.5)
		"win":
			return S.sequence([S.note("C5", 0.1), S.note("E5", 0.1), S.note("G5", 0.1), S.note("C6", 0.3)], S.Wave.SQUARE, 0.75)
		"loss":
			return S.sequence([S.note("E4", 0.18), S.note("C4", 0.3)], S.Wave.SINE, 0.55)
		"ask":
			return S.sequence([S.note("E5", 0.07), S.note("A5", 0.1)], S.Wave.TRIANGLE, 0.55)
		"music_loop":
			var melody := [
				S.note("C5", 0.3), S.note("E5", 0.3), S.note("G5", 0.3), S.note("E5", 0.3),
				S.note("C5", 0.3), S.note("D5", 0.3), S.note("E5", 0.3), S.note("G5", 0.5),
				S.note("F5", 0.3), S.note("E5", 0.3), S.note("D5", 0.3), S.note("C5", 0.5),
			]
			var w := S.sequence(melody, S.Wave.SQUARE, 0.35, 0.01)
			w.loop_mode = AudioStreamWAV.LOOP_FORWARD
			w.loop_begin = 0
			w.loop_end = w.data.size() / 2  # sample count
			return w
	push_error("CCAudio: unknown sound '%s'" % key)
	return null
