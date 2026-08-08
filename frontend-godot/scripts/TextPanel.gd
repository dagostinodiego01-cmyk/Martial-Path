extends PanelContainer
## Reusable labelled rich-text panel for Godot frontend views.
##
## This component is presentation-only. Parent controllers provide already
## prepared display text from backend state/results.

@onready var title_label: Label = $VBox/Title
@onready var text_label: RichTextLabel = $VBox/Text


func set_title(value: String) -> void:
	if title_label == null:
		$VBox/Title.text = value
		return
	title_label.text = value


func set_text(value: String) -> void:
	if text_label == null:
		$VBox/Text.clear()
		$VBox/Text.append_text(value)
		return
	text_label.clear()
	text_label.append_text(value)
