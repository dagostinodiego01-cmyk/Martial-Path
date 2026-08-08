"""Central data validation for shipped game content.

Public entry point:

    from game.validation import validate_all_game_data
    result = validate_all_game_data()
    assert result.is_valid, result.format_errors()
"""
from game.validation.data_validator import validate_all_game_data
from game.validation.validation_error import ValidationError, ValidationResult

__all__ = ["validate_all_game_data", "ValidationResult", "ValidationError"]
