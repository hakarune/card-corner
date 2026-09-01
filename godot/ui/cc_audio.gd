extends Node
## Autoload: sound effects + music. STUB for now -- every call is a safe
## no-op so screen code can be written final; Phase 7 fills in the synth
## (AudioStreamGenerator) and real playback + mute/volume handling.

var muted := false
var sfx_volume := 0.8
var music_volume := 0.4


func play_sfx(_name: String) -> void:
	pass


func start_music() -> void:
	pass


func stop_music() -> void:
	pass


func set_muted(value: bool) -> void:
	muted = value
