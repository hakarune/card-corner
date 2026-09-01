class_name ThemeData
extends RefCounted
## Shared kid-friendly palette, sizing, and per-game card themes.
## Ported from legacy/ui/theme.py (renamed to avoid clashing with Godot's
## built-in `Theme` resource type). All-static; never instantiated.

const WINDOW_SIZE := Vector2i(1024, 720)

# -- Palette (Color8 = 0-255 sRGB, matching the legacy tuples) --------------
const BACKGROUND := Color8(255, 248, 231)   # warm cream
const PANEL := Color8(255, 255, 255)
const PRIMARY := Color8(255, 107, 107)      # coral red
const PRIMARY_DARK := Color8(222, 74, 74)
const SECONDARY := Color8(69, 191, 181)     # teal
const ACCENT := Color8(255, 195, 74)        # sunny yellow
const SUCCESS := Color8(123, 199, 88)       # grass green
const TEXT_DARK := Color8(45, 45, 65)
const TEXT_LIGHT := Color8(255, 255, 255)
const TEXT_MUTED := Color8(120, 120, 138)

const CARD_BACK := Color8(91, 134, 229)
const CARD_BACK_PATTERN := Color8(255, 255, 255)
const CARD_FACE := Color8(255, 255, 255)
const CARD_BORDER := Color8(45, 45, 65)
const CARD_RED := Color8(219, 58, 58)
const CARD_BLACK := Color8(52, 52, 66)

const GAME_COLORS := {
	"go_fish": Color8(91, 155, 213),
	"old_maid": Color8(176, 120, 219),
	"memory": Color8(123, 199, 88),
	"letter_match": Color8(255, 165, 90),
}

const MIN_TOUCH_TARGET := 88  # px


## A pale, pastel version of `color` (legacy _tint, amount=0.82).
static func tint(color: Color, amount := 0.82) -> Color:
	return Color(
		color.r + (1.0 - color.r) * amount,
		color.g + (1.0 - color.g) * amount,
		color.b + (1.0 - color.b) * amount,
		1.0,
	)


static func card_themes() -> Dictionary:
	# Built lazily (const dicts can't hold objects). Callers may cache.
	return {
		"go_fish": CardTheme.new("GO FISH!", GAME_COLORS["go_fish"], "fish",
			tint(GAME_COLORS["go_fish"]), "go_fish"),
		"old_maid": CardTheme.new("OLD MAID", GAME_COLORS["old_maid"], "crown",
			tint(GAME_COLORS["old_maid"]), "old_maid"),
		"memory": CardTheme.new("MEMORY", GAME_COLORS["memory"], "puzzle",
			tint(GAME_COLORS["memory"]), "memory"),
	}


static func card_theme(key: String) -> CardTheme:
	return card_themes()[key]
