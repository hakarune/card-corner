class_name MenuToggle
extends Control
## A small square toggle button drawn procedurally (no font/emoji needed).
## `kind` is "fullscreen" or "mute". Ported from _draw_icon_buttons in
## legacy/ui/launcher.py.

signal pressed

@export_enum("fullscreen", "mute") var kind := "fullscreen"

var _active := false  ## fullscreen: is fullscreen; mute: is muted
var _hovered := false


func set_active(value: bool) -> void:
	if _active != value:
		_active = value
		queue_redraw()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		pressed.emit()
		accept_event()


func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_ENTER:
		_hovered = true
		queue_redraw()
	elif what == NOTIFICATION_MOUSE_EXIT:
		_hovered = false
		queue_redraw()


func _draw() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var sb := StyleBoxFlat.new()
	sb.bg_color = ThemeData.PANEL if not _hovered else ThemeData.PANEL.darkened(0.05)
	sb.set_corner_radius_all(10)
	sb.set_border_width_all(2)
	sb.border_color = ThemeData.TEXT_DARK
	draw_style_box(sb, full)

	var c := full.get_center()
	if kind == "fullscreen":
		_draw_fullscreen(c)
	else:
		_draw_mute(c)


func _draw_fullscreen(c: Vector2) -> void:
	var col := ThemeData.TEXT_DARK
	var pad := size.x * 0.24
	var arm := size.x * 0.18
	# four corners; brackets point outward normally, inward when fullscreen
	var pts := [
		[Vector2(pad, pad), Vector2(1, 1)],
		[Vector2(size.x - pad, pad), Vector2(-1, 1)],
		[Vector2(pad, size.y - pad), Vector2(1, -1)],
		[Vector2(size.x - pad, size.y - pad), Vector2(-1, -1)],
	]
	for p in pts:
		var o: Vector2 = p[0]
		var d: Vector2 = p[1]
		if _active:
			o += Vector2(-d.x, -d.y) * arm  # pull the corner inward
		draw_line(o, o + Vector2(d.x * arm, 0), col, 3.0)
		draw_line(o, o + Vector2(0, d.y * arm), col, 3.0)


func _draw_mute(c: Vector2) -> void:
	var col := ThemeData.TEXT_DARK
	var u := size.x / 44.0  # legacy glyph was authored on an ~44px target
	var body := PackedVector2Array([
		c + Vector2(-14, -6) * u, c + Vector2(-6, -6) * u, c + Vector2(4, -14) * u,
		c + Vector2(4, 14) * u, c + Vector2(-6, 6) * u, c + Vector2(-14, 6) * u,
	])
	draw_colored_polygon(body, col)
	if _active:  # muted: red X
		var red := Color8(196, 90, 90)
		draw_line(c + Vector2(8, -10) * u, c + Vector2(18, 10) * u, red, 3.0)
		draw_line(c + Vector2(18, -10) * u, c + Vector2(8, 10) * u, red, 3.0)
	else:  # sound on: a little wave arc
		draw_arc(c + Vector2(6, 0) * u, 12.0 * u, -0.9, 0.9, 12, col, 2.0)
