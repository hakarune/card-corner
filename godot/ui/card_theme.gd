class_name CardTheme
extends RefCounted
## A game's complete card visual identity. Ported from legacy/ui/theme.py.

var label: String            ## lettered across the card back ("GO FISH!" etc.)
var back_color: Color        ## the back's base color
var pattern: String          ## corner-pattern key: "fish" | "crown" | "puzzle"
var front_tint: Color        ## pale non-white tint for card fronts
var asset_key: String        ## key for res://assets/cards/backs/<key>.*


func _init(p_label: String, p_back_color: Color, p_pattern: String,
		p_front_tint: Color, p_asset_key: String) -> void:
	label = p_label
	back_color = p_back_color
	pattern = p_pattern
	front_tint = p_front_tint
	asset_key = p_asset_key
