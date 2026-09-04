"""Tests for the narrative-template linter (ROADMAP A.7)."""
from game.data.registry import GameDataRegistry
from game.validation.narrative_lint import lint_narrative_templates


def _shipped_templates():
    return GameDataRegistry.load().narrative_templates


def test_shipped_templates_lint_clean():
    assert lint_narrative_templates(_shipped_templates()) == []


def test_detects_undeclared_slot():
    templates = {"v": {"variables": [], "variants": [{"weight": 1, "template": "Hello {name}"}]}}
    assert any("undeclared slot" in message for _category, message in lint_narrative_templates(templates))


def test_detects_unused_variable():
    templates = {"v": {"variables": ["name"], "variants": [{"weight": 1, "template": "plain text"}]}}
    assert any("unused variable" in message for _category, message in lint_narrative_templates(templates))


def test_detects_unknown_when_op():
    templates = {
        "v": {"variables": [], "variants": [{"weight": 1, "template": "x", "when": {"field": "season", "op": "??", "value": "Spring"}}]}
    }
    assert any("unknown op" in message for _category, message in lint_narrative_templates(templates))


def test_detects_missing_event_coverage():
    assert any("maps to missing" in message for _category, message in lint_narrative_templates({}))
