class_name ItemIcons
extends RefCounted
## Kid-themed item glyphs for each card rank (sun, moon, star, ...) and the
## Letter Match animal set. Ported from legacy/ui/items.py -- the same
## procedural shapes, drawn into a CanvasItem via _draw().
##
## These are the built-in FALLBACK. draw_item()/draw_animal() first look for
## real art at res://assets/icons/{items,animals}/<key>.<png|svg> and use
## that instead when present (keys are the lowercased item/animal name).

# name -> draw function name (called as ItemIcons.call(fn, ci, rect, color))
const RANK_ITEMS := {
	Card.Rank.ACE: "Sun", Card.Rank.TWO: "Moon", Card.Rank.THREE: "Star",
	Card.Rank.FOUR: "Heart", Card.Rank.FIVE: "Flower", Card.Rank.SIX: "Fish",
	Card.Rank.SEVEN: "Bird", Card.Rank.EIGHT: "Tree", Card.Rank.NINE: "House",
	Card.Rank.TEN: "Umbrella", Card.Rank.JACK: "Apple", Card.Rank.QUEEN: "Ball",
	Card.Rank.KING: "Boat",
}

# Letter Match "animals" mode: starting letter -> animal name. Keys must match
# games.letter_match ANIMAL_MODE_LETTERS.
const ANIMAL_ICONS := {
	"B": "Bird", "C": "Cat", "D": "Dog", "F": "Fish", "L": "Lion", "O": "Owl", "P": "Pig",
}

const _IRREGULAR_PLURALS := {"Fish": "Fish"}


static func item_name(rank: int) -> String:
	return RANK_ITEMS[rank]


static func item_name_plural(rank: int) -> String:
	var n: String = RANK_ITEMS[rank]
	return _IRREGULAR_PLURALS.get(n, n + "s")


## Loads real art for an item/animal name, or null if none is committed yet.
static func load_art(name: String) -> Texture2D:
	var key := name.to_lower()
	for sub: String in ["items", "animals"]:
		for ext: String in ["png", "svg", "jpg"]:
			var path := "res://assets/icons/%s/%s.%s" % [sub, key, ext]
			if ResourceLoader.exists(path):
				return load(path) as Texture2D
	return null


static func draw_item(ci: CanvasItem, rect: Rect2, rank: int, color: Color) -> void:
	_draw_named(ci, rect, RANK_ITEMS[rank], color)


static func draw_animal(ci: CanvasItem, rect: Rect2, letter: String, color: Color) -> void:
	_draw_named(ci, rect, ANIMAL_ICONS[letter], color)


static func _draw_named(ci: CanvasItem, rect: Rect2, name: String, color: Color) -> void:
	var tex := load_art(name)
	if tex != null:
		var tw := float(tex.get_width())
		var th := float(tex.get_height())
		var scale: float = min(rect.size.x / tw, rect.size.y / th)
		var sz := Vector2(tw * scale, th * scale)
		ci.draw_texture_rect(tex, Rect2(rect.get_center() - sz * 0.5, sz), false)
		return
	match name:
		"Sun": _sun(ci, rect, color)
		"Moon": _moon(ci, rect, color)
		"Star": _star(ci, rect, color)
		"Heart": _heart(ci, rect, color)
		"Flower": _flower(ci, rect, color)
		"Fish": _fish(ci, rect, color)
		"Bird": _bird(ci, rect, color)
		"Tree": _tree(ci, rect, color)
		"House": _house(ci, rect, color)
		"Umbrella": _umbrella(ci, rect, color)
		"Apple": _apple(ci, rect, color)
		"Ball": _ball(ci, rect, color)
		"Boat": _boat(ci, rect, color)
		"Cat": _cat(ci, rect, color)
		"Dog": _dog(ci, rect, color)
		"Lion": _lion(ci, rect, color)
		"Owl": _owl(ci, rect, color)
		"Pig": _pig(ci, rect, color)


# -- ellipse helper (Godot has no draw_ellipse) ----------------------------
static func _ellipse(ci: CanvasItem, center: Vector2, rx: float, ry: float, color: Color) -> void:
	var pts := PackedVector2Array()
	var steps := 24
	for i in steps:
		var a := TAU * i / steps
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	ci.draw_colored_polygon(pts, color)


static func _ellipse_rect(ci: CanvasItem, r: Rect2, color: Color) -> void:
	_ellipse(ci, r.get_center(), r.size.x * 0.5, r.size.y * 0.5, color)


static func _lighter(c: Color, amt := 60.0) -> Color:
	var d := amt / 255.0
	return Color(minf(1.0, c.r + d), minf(1.0, c.g + d), minf(1.0, c.b + d), c.a)


# -- the glyphs (mirrors legacy/ui/items.py) -------------------------------
static func _sun(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.18
	ci.draw_circle(c, r, color)
	for i in 8:
		var a := i * PI / 4.0
		var p1 := c + Vector2(cos(a), sin(a)) * r * 1.4
		var p2 := c + Vector2(cos(a), sin(a)) * r * 2.0
		ci.draw_line(p1, p2, color, 3.0)


static func _moon(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.22
	ci.draw_circle(c, r, color)
	ci.draw_circle(c + Vector2(r * 0.55, 0), r * 0.8, _lighter(color))


static func _star(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.22
	var pts := PackedVector2Array()
	for i in 10:
		var a := i * PI / 5.0 - PI / 2.0
		var radius := r if i % 2 == 0 else r * 0.42
		pts.append(c + Vector2(cos(a), sin(a)) * radius)
	ci.draw_colored_polygon(pts, color)


static func _heart(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.16
	ci.draw_circle(c + Vector2(-s * 0.5, -s * 0.2), s * 0.6, color)
	ci.draw_circle(c + Vector2(s * 0.5, -s * 0.2), s * 0.6, color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-s, -s * 0.1), c + Vector2(s, -s * 0.1), c + Vector2(0, s * 1.2),
	]), color)


static func _flower(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.12
	for i in 5:
		var a := i * TAU / 5.0
		ci.draw_circle(c + Vector2(cos(a), sin(a)) * r * 1.6, r, color)
	ci.draw_circle(c, r * 0.9, color)


static func _fish(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var w: float = min(rect.size.x, rect.size.y) * 0.3
	_ellipse_rect(ci, Rect2(c + Vector2(-w * 0.5, -w * 0.4), Vector2(w * 1.4, w * 0.8)), color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-w * 0.5, 0), c + Vector2(-w, -w * 0.4), c + Vector2(-w, w * 0.4),
	]), color)


static func _bird(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.2
	_ellipse(ci, c + Vector2(0, s * 0.15), s * 0.8, s * 0.65, color)
	var head := c + Vector2(-s * 0.55, -s * 0.55)
	ci.draw_circle(head, s * 0.55, color)
	ci.draw_colored_polygon(PackedVector2Array([
		head + Vector2(-s * 0.55, 0), head + Vector2(-s * 0.95, -s * 0.12), head + Vector2(-s * 0.95, s * 0.12),
	]), color)
	_ellipse(ci, c + Vector2(s * 0.15, s * 0.1), s * 0.4, s * 0.3, _lighter(color))


static func _tree(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.18
	ci.draw_rect(Rect2(c + Vector2(-s * 0.15, 0), Vector2(s * 0.3, s * 1.1)), color)
	ci.draw_circle(c + Vector2(0, -s * 0.3), s * 0.9, color)


static func _house(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.17
	ci.draw_rect(Rect2(c + Vector2(-s * 0.8, s * 0.4 - s * 0.55), Vector2(s * 1.6, s * 1.1)), color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-s, -s * 0.1), c + Vector2(0, -s * 1.3), c + Vector2(s, -s * 0.1),
	]), color)


static func _umbrella(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.2
	ci.draw_arc(c, s, PI, TAU, 24, color, maxf(3.0, s * 0.3))
	ci.draw_line(c, c + Vector2(0, s * 1.3), color, 3.0)


static func _apple(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.2
	ci.draw_circle(c + Vector2(-r * 0.5, 0), r, color)
	ci.draw_circle(c + Vector2(r * 0.5, 0), r, color)
	ci.draw_line(c + Vector2(0, -r), c + Vector2(0, -r * 1.7), color, 3.0)


static func _ball(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.22
	ci.draw_circle(c, r, color, false, maxf(3.0, r * 0.25))
	ci.draw_line(c + Vector2(-r, 0), c + Vector2(r, 0), color, 2.0)
	ci.draw_line(c + Vector2(0, -r), c + Vector2(0, r), color, 2.0)


static func _boat(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var s: float = min(rect.size.x, rect.size.y) * 0.2
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-s * 1.3, 0), c + Vector2(s * 1.3, 0),
		c + Vector2(s * 0.8, s * 0.7), c + Vector2(-s * 0.8, s * 0.7),
	]), color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(0, -s * 1.4), c + Vector2(0, 0), c + Vector2(s * 0.9, 0),
	]), color)


static func _cat(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.2
	ci.draw_circle(c, r, color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-r * 0.8, -r * 0.5), c + Vector2(-r * 0.2, -r * 0.5), c + Vector2(-r * 0.6, -r * 1.3),
	]), color)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(r * 0.8, -r * 0.5), c + Vector2(r * 0.2, -r * 0.5), c + Vector2(r * 0.6, -r * 1.3),
	]), color)


static func _dog(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.18
	ci.draw_circle(c + Vector2(0, -r * 0.2), r, color)
	_ellipse_rect(ci, Rect2(c + Vector2(-r * 1.3, -r * 0.6), Vector2(r * 0.6, r * 1.3)), color)
	_ellipse_rect(ci, Rect2(c + Vector2(r * 0.7, -r * 0.6), Vector2(r * 0.6, r * 1.3)), color)
	_ellipse_rect(ci, Rect2(c + Vector2(-r * 0.45, r * 0.4), Vector2(r * 0.9, r * 0.6)), color)


static func _lion(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.22
	var lite := _lighter(color, 50.0)
	ci.draw_circle(c, r * 1.35, lite)
	for dx in [-1.0, 1.0]:
		ci.draw_circle(c + Vector2(dx * r * 1.1, -r * 0.9), r * 0.5, lite)
	ci.draw_circle(c, r * 0.85, color)
	for dx in [-1.0, 1.0]:
		ci.draw_circle(c + Vector2(dx * r * 0.6, -r * 0.7), r * 0.25, color)


static func _owl(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.22
	ci.draw_circle(c, r, color)
	var lite := _lighter(color)
	ci.draw_circle(c + Vector2(-r * 0.4, -r * 0.1), r * 0.35, lite)
	ci.draw_circle(c + Vector2(r * 0.4, -r * 0.1), r * 0.35, lite)
	ci.draw_colored_polygon(PackedVector2Array([
		c + Vector2(-r * 0.15, r * 0.15), c + Vector2(r * 0.15, r * 0.15), c + Vector2(0, r * 0.45),
	]), color)


static func _pig(ci: CanvasItem, rect: Rect2, color: Color) -> void:
	var c := rect.get_center()
	var r: float = min(rect.size.x, rect.size.y) * 0.2
	ci.draw_circle(c, r, color)
	ci.draw_circle(c + Vector2(-r * 0.75, -r * 0.75), r * 0.35, color)
	ci.draw_circle(c + Vector2(r * 0.75, -r * 0.75), r * 0.35, color)
	var lite := _lighter(color, 90.0)
	_ellipse_rect(ci, Rect2(c + Vector2(-r * 0.45, r * 0.35 - r * 0.3), Vector2(r * 0.9, r * 0.6)), lite)
	ci.draw_circle(c + Vector2(-r * 0.18, r * 0.35), r * 0.07, color)
	ci.draw_circle(c + Vector2(r * 0.18, r * 0.35), r * 0.07, color)
