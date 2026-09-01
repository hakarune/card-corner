class_name CardView
extends Control
## Draws one card/tile and reports clicks. Ported from the card/tile drawing
## helpers in legacy/ui/widgets.py. Real art in res://assets/... overrides
## the procedural fallback where it exists.

enum Mode { BLANK, BACK, ITEM_FACE, PIP_FACE, OLD_MAID, LETTER, ANIMAL }

signal clicked(view: CardView)

var mode: int = Mode.BLANK
var card_theme: CardTheme = null
var card: Card = null           ## model card (ITEM_FACE / PIP_FACE / OLD_MAID)
var text := ""                  ## LETTER tile glyph
var letter := ""                ## ANIMAL tile: the starting letter key
var accent := Color.WHITE       ## LETTER / ANIMAL tile color
var highlighted := false        ## pulsing accent border
var face_down := false          ## BACK when true, else the configured face

var _pulse_t := 0.0
var _tex_cache := {}


func setup(p_mode: int, p_theme: CardTheme = null, p_card: Card = null) -> void:
	mode = p_mode
	card_theme = p_theme
	card = p_card
	queue_redraw()


func setup_letter(p_mode: int, p_text: String, p_letter: String, p_color: Color) -> void:
	mode = p_mode
	text = p_text
	letter = p_letter
	accent = p_color
	queue_redraw()


func set_highlighted(on: bool) -> void:
	if highlighted == on:
		return
	highlighted = on
	set_process(on)
	queue_redraw()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_process(false)


func _process(delta: float) -> void:
	_pulse_t += delta
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		clicked.emit(self)
		accept_event()


# -- helpers ----------------------------------------------------------------
func _box(bg: Color, border: Color, radius: int, border_w: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.set_corner_radius_all(radius)
	sb.set_border_width_all(border_w)
	sb.border_color = border
	return sb


func _font() -> Font:
	return ThemeDB.fallback_font


func _draw_center_text(t: String, px: int, color: Color, offset_y := 0.0) -> void:
	var f := _font()
	var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_CENTER, -1, px)
	f.draw_string(get_canvas_item(), Vector2(0, size.y * 0.5 + px * 0.35 + offset_y),
		t, HORIZONTAL_ALIGNMENT_CENTER, size.x, px, color)


func _fit_bottom_label(t: String, max_w: float, px: int, color: Color) -> void:
	var f := _font()
	var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_CENTER, -1, px).x
	var use_px := px
	if w > max_w and w > 0:
		use_px = int(px * max_w / w)
	f.draw_string(get_canvas_item(), Vector2(0, size.y - 8), t,
		HORIZONTAL_ALIGNMENT_CENTER, size.x, use_px, color)


func _tex(path_no_ext: String) -> Texture2D:
	if _tex_cache.has(path_no_ext):
		return _tex_cache[path_no_ext]
	var tex: Texture2D = null
	for ext: String in ["png", "svg", "jpg"]:
		var p := path_no_ext + "." + ext
		if ResourceLoader.exists(p):
			tex = load(p)
			break
	_tex_cache[path_no_ext] = tex
	return tex


func _draw() -> void:
	var m := mode
	if face_down:
		m = Mode.BACK
	match m:
		Mode.BACK: _draw_back()
		Mode.ITEM_FACE: _draw_item_face()
		Mode.PIP_FACE: _draw_pip_face()
		Mode.OLD_MAID: _draw_old_maid()
		Mode.LETTER: _draw_letter_tile()
		Mode.ANIMAL: _draw_animal_tile()
	_draw_highlight()


func _draw_highlight() -> void:
	if not highlighted:
		return
	var pulse := 4.0 + 3.0 * (0.5 + 0.5 * sin(_pulse_t * 6.6))
	draw_style_box(_box(Color.TRANSPARENT, ThemeData.ACCENT, 14, int(pulse)),
		Rect2(Vector2(-5, -5), size + Vector2(10, 10)))


func _draw_back() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var t := card_theme
	if t == null:
		draw_style_box(_box(ThemeData.CARD_BACK, ThemeData.CARD_BORDER, 12, 3), full)
		var c := full.get_center()
		var r: float = min(size.x, size.y) / 5.0
		draw_circle(c, r, ThemeData.CARD_BACK_PATTERN, false, 4.0)
		draw_circle(c, maxf(r - 14.0, 4.0), ThemeData.CARD_BACK_PATTERN)
		return
	var tex := _tex("res://assets/cards/backs/" + t.asset_key)
	draw_style_box(_box(t.back_color, t.back_color, 12, 0), full)
	if tex != null:
		draw_texture_rect(tex, full, false)
		draw_style_box(_box(Color.TRANSPARENT, ThemeData.CARD_BORDER, 12, 3), full)
		_fit_bottom_label(t.label, size.x * 0.85, maxi(int(size.y * 0.13), 11), ThemeData.TEXT_LIGHT)
		return
	draw_style_box(_box(t.back_color, ThemeData.CARD_BORDER, 12, 3), full)
	if size.x >= 85.0:
		var s: float = min(size.x, size.y) * 0.11
		var mx := size.x * 0.2
		var my := size.y * 0.16
		for cx in [mx, size.x - mx]:
			for cy in [my, size.y - my]:
				_draw_pattern(t.pattern, Vector2(cx, cy), s, ThemeData.TEXT_LIGHT)
	_fit_bottom_label(t.label, size.x * 0.85, maxi(int(size.y * 0.13), 11), ThemeData.TEXT_LIGHT)


func _draw_item_face() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var t := card_theme
	draw_style_box(_box(t.front_tint, t.back_color, 12, 3), full)
	var icon_area := Rect2(size.x * 0.15, size.y * 0.225 - size.y * 0.08,
		size.x * 0.7, size.y * 0.55)
	ItemIcons.draw_item(self, icon_area, card.rank, t.back_color)
	_fit_bottom_label(ItemIcons.item_name(card.rank), size.x * 0.85,
		maxi(int(size.y * 0.13), 11), ThemeData.TEXT_DARK)


func _draw_pip_face() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var t := card_theme
	var bg := t.front_tint if t != null else ThemeData.CARD_FACE
	var border := t.back_color if t != null else ThemeData.CARD_BORDER
	draw_style_box(_box(bg, border, 12, 3), full)
	var col := ThemeData.CARD_RED if card.is_red() else ThemeData.CARD_BLACK
	var f := _font()
	f.draw_string(get_canvas_item(), Vector2(8, 6 + int(size.y * 0.16)), card.label(),
		HORIZONTAL_ALIGNMENT_LEFT, -1, maxi(int(size.y * 0.16), 12), col)
	_draw_center_text(card.symbol(), maxi(int(size.y * 0.38), 16), col)


func _draw_old_maid() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var t := ThemeData.card_theme("old_maid")
	draw_style_box(_box(t.front_tint, t.back_color, 12, 3), full)

	var front := _tex("res://assets/cards/fronts/old_maid")
	if front != null:
		draw_texture_rect(front, full, false)
		draw_style_box(_box(Color.TRANSPARENT, t.back_color, 12, 3), full)
		_fit_bottom_label("OLD MAID", size.x * 0.9, maxi(int(size.y * 0.1), 10), t.back_color)
		return
	var icon := _tex("res://assets/icons/special/old_maid_card")
	if icon != null:
		var pad_x := size.x * 0.15
		var pad_y := size.y * 0.15
		var iw := float(icon.get_width())
		var ih := float(icon.get_height())
		var scale: float = min((size.x - 2 * pad_x) / iw, (size.y - 2 * pad_y) / ih)
		var sz := Vector2(iw * scale, ih * scale)
		draw_texture_rect(icon, Rect2(Vector2(size.x, size.y) * 0.5 - sz * 0.5 - Vector2(0, size.y * 0.05), sz), false)
		_fit_bottom_label("OLD MAID", size.x * 0.9, maxi(int(size.y * 0.1), 10), t.back_color)
		return
	_draw_granny(t)
	_fit_bottom_label("OLD MAID", size.x * 0.9, maxi(int(size.y * 0.1), 10), t.back_color)


func _draw_granny(t: CardTheme) -> void:
	var cx := size.x * 0.5
	var cy := size.y * 0.5 + size.y * 0.06
	var head_r := size.x * 0.28
	var skin := Color8(247, 214, 180)
	draw_colored_polygon(PackedVector2Array([
		Vector2(cx - head_r * 1.3, cy - head_r * 0.2),
		Vector2(cx, cy - head_r * 1.9),
		Vector2(cx + head_r * 1.3, cy - head_r * 0.2),
	]), t.back_color)
	draw_circle(Vector2(cx, cy), head_r, skin)
	var eye_dx := head_r * 0.42
	var eye_y := cy - head_r * 0.05
	var gr := head_r * 0.3
	for dx in [-eye_dx, eye_dx]:
		draw_circle(Vector2(cx + dx, eye_y), gr, ThemeData.TEXT_DARK, false, 3.0)
		draw_circle(Vector2(cx + dx, eye_y), gr * 0.35, ThemeData.TEXT_DARK)
	draw_line(Vector2(cx - eye_dx + gr, eye_y), Vector2(cx + eye_dx - gr, eye_y), ThemeData.TEXT_DARK, 2.0)
	for dx in [-head_r * 0.55, head_r * 0.55]:
		draw_circle(Vector2(cx + dx, cy + head_r * 0.35), head_r * 0.18, Color8(240, 150, 150))
	draw_arc(Vector2(cx, cy + head_r * 0.3), head_r * 0.45, 0.55, 2.6, 20, ThemeData.TEXT_DARK, 3.0)


func _draw_letter_tile() -> void:
	var full := Rect2(Vector2.ZERO, size)
	draw_style_box(_box(ThemeData.tint(accent), accent, 14, 5), full)
	_draw_center_text(text, maxi(int(size.y * 0.55), 18), ThemeData.TEXT_DARK)


func _draw_animal_tile() -> void:
	var full := Rect2(Vector2.ZERO, size)
	draw_style_box(_box(ThemeData.tint(accent), accent, 14, 5), full)
	ItemIcons.draw_animal(self, full, letter, ThemeData.TEXT_DARK)


func _draw_pattern(kind: String, c: Vector2, s: float, color: Color) -> void:
	match kind:
		"fish":
			draw_colored_polygon(PackedVector2Array([
				c + Vector2(-s, 0), c + Vector2(-s * 0.15, -s * 0.55), c + Vector2(-s * 0.15, s * 0.55),
			]), color)
			draw_circle(c + Vector2(s * 0.35, 0), s * 0.45, color)
		"crown":
			draw_colored_polygon(PackedVector2Array([
				c + Vector2(-s, s * 0.5), c + Vector2(-s, -s * 0.1), c + Vector2(-s * 0.5, s * 0.15),
				c + Vector2(0, -s * 0.55), c + Vector2(s * 0.5, s * 0.15), c + Vector2(s, -s * 0.1),
				c + Vector2(s, s * 0.5),
			]), color)
		"puzzle":
			draw_circle(c, s * 0.5, color, false, maxf(2.0, s * 0.15))
			draw_circle(c, s * 0.2, color)
