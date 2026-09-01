class_name Synth
extends RefCounted
## Procedural audio synthesis. Ported from legacy/audio/synth.py -- every
## sound in the game is generated from simple waveforms, no external asset.
## Produces AudioStreamWAV (16-bit signed PCM, mono, 44100 Hz), the Godot
## analogue of pygame.mixer.Sound(buffer=...).

const SAMPLE_RATE := 44100
const AMPLITUDE := 24000.0  # headroom below int16 max so mixing doesn't clip

enum Wave { SINE, SQUARE, TRIANGLE }

const NOTES := {
	"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
	"G4": 392.00, "A4": 440.00, "B4": 493.88,
	"C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
	"G5": 783.99, "A5": 880.00, "B5": 987.77, "C6": 1046.50,
}


static func _wave(shape: int, phase: float) -> float:
	var theta := fposmod(phase, 1.0)
	match shape:
		Wave.SQUARE:
			return 1.0 if theta < 0.5 else -1.0
		Wave.TRIANGLE:
			return 4.0 * absf(theta - 0.5) - 1.0
		_:
			return sin(TAU * theta)


static func _envelope(i: int, n: int, attack: int, release: int) -> float:
	if i < attack:
		return float(i) / attack
	if i > n - release:
		return maxf(0.0, float(n - i) / release)
	return 1.0


static func _clamp16(value: float) -> int:
	return clampi(int(value), -32768, 32767)


static func _wav(samples: PackedByteArray) -> AudioStreamWAV:
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SAMPLE_RATE
	w.stereo = false
	w.data = samples
	return w


## A single note. `freq <= 0` -> silence of the given duration.
static func tone(freq: float, duration: float, shape: int = Wave.SINE, volume: float = 1.0) -> AudioStreamWAV:
	var n: int = max(1, int(SAMPLE_RATE * duration))
	var attack: int = max(1, int(n * 0.05))
	var release: int = max(1, int(n * 0.2))
	var buf := PackedByteArray()
	buf.resize(n * 2)
	if freq > 0.0:
		for i in n:
			var phase := freq * i / SAMPLE_RATE
			var env := _envelope(i, n, attack, release)
			buf.encode_s16(i * 2, _clamp16(AMPLITUDE * volume * env * _wave(shape, phase)))
	return _wav(buf)


## A note whose pitch glides linearly start_freq -> end_freq.
static func sweep(start_freq: float, end_freq: float, duration: float,
		shape: int = Wave.SINE, volume: float = 1.0) -> AudioStreamWAV:
	var n: int = max(1, int(SAMPLE_RATE * duration))
	var attack: int = max(1, int(n * 0.05))
	var release: int = max(1, int(n * 0.25))
	var buf := PackedByteArray()
	buf.resize(n * 2)
	var phase := 0.0
	for i in n:
		var t := float(i) / n
		var freq := start_freq + (end_freq - start_freq) * t
		phase += freq / SAMPLE_RATE
		var env := _envelope(i, n, attack, release)
		buf.encode_s16(i * 2, _clamp16(AMPLITUDE * volume * env * _wave(shape, phase)))
	return _wav(buf)


## A short melody. `notes` = Array of [freq_hz, duration_s]; freq <= 0 is a rest.
static func sequence(notes: Array, shape: int = Wave.SQUARE,
		volume: float = 1.0, gap: float = 0.015) -> AudioStreamWAV:
	var gap_n := int(SAMPLE_RATE * gap)
	var segments: Array = []  # [freq, n]
	var total_n := 0
	for note in notes:
		var seg_n: int = max(1, int(SAMPLE_RATE * note[1]))
		segments.append([note[0], seg_n])
		total_n += seg_n + gap_n

	var buf := PackedByteArray()
	buf.resize(total_n * 2)
	var idx := 0
	for seg in segments:
		var freq: float = seg[0]
		var seg_n: int = seg[1]
		if freq > 0.0:
			var attack: int = max(1, int(seg_n * 0.05))
			var release: int = max(1, int(seg_n * 0.15))
			for i in seg_n:
				var phase := freq * i / SAMPLE_RATE
				var env := _envelope(i, seg_n, attack, release)
				buf.encode_s16((idx + i) * 2, _clamp16(AMPLITUDE * volume * env * _wave(shape, phase)))
		idx += seg_n + gap_n
	return _wav(buf)


static func note(name: String, dur: float) -> Array:
	return [NOTES[name], dur]
