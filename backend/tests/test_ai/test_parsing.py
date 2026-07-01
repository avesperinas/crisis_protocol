import pytest

from src.ai.parsing import ParseError, parse_evaluation_json
from src.engine.types import ActionType


CLEAN_JSON = """{
  "evaluations": [
    {
      "player_id": "macedonia",
      "action_type": "military_offensive",
      "target_id": "atenas",
      "coherence_score": 0.85,
      "posture_modifier": 0.10,
      "decision_quality": 7.5,
      "decision_quality_reasoning": "good move",
      "effective_multiplier": 1.05
    }
  ]
}"""


def test_parses_clean_json() -> None:
    parsed = parse_evaluation_json(CLEAN_JSON)
    assert len(parsed.evaluations) == 1
    eval_ = parsed.evaluations[0]
    assert eval_.player_id == "macedonia"
    assert eval_.action_type_enum() == ActionType.MILITARY_OFFENSIVE
    assert eval_.target_id == "atenas"
    assert eval_.coherence_score == 0.85


def test_parses_json_inside_markdown_fences() -> None:
    text = f"```json\n{CLEAN_JSON}\n```"
    parsed = parse_evaluation_json(text)
    assert len(parsed.evaluations) == 1


def test_parses_json_with_surrounding_prose() -> None:
    text = f"Here is the JSON you requested:\n\n{CLEAN_JSON}\n\nLet me know if you need more."
    parsed = parse_evaluation_json(text)
    assert len(parsed.evaluations) == 1


def test_unknown_action_type_falls_back_to_generic_enum() -> None:
    text = """{"evaluations": [{
      "player_id": "x", "action_type": "wat", "target_id": null,
      "coherence_score": 0.5, "decision_quality": 5
    }]}"""
    parsed = parse_evaluation_json(text)
    assert parsed.evaluations[0].action_type_enum() == ActionType.GENERIC


def test_invalid_json_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        parse_evaluation_json("not even close to json")


def test_validation_failure_raises_parse_error() -> None:
    # coherence_score out of range
    text = """{"evaluations": [{
      "player_id": "x", "action_type": "generic", "target_id": null,
      "coherence_score": 9.9, "decision_quality": 5
    }]}"""
    with pytest.raises(ParseError):
        parse_evaluation_json(text)


def test_missing_required_field_raises_parse_error() -> None:
    text = """{"evaluations": [{"player_id": "x"}]}"""
    with pytest.raises(ParseError):
        parse_evaluation_json(text)


def test_handles_multiple_evaluations() -> None:
    text = """{
      "evaluations": [
        {"player_id": "a", "action_type": "generic", "target_id": null,
         "coherence_score": 0.5, "decision_quality": 5},
        {"player_id": "b", "action_type": "diplomatic_proposal", "target_id": "a",
         "coherence_score": 0.9, "decision_quality": 8, "effective_multiplier": 1.1}
      ]
    }"""
    parsed = parse_evaluation_json(text)
    assert len(parsed.evaluations) == 2
    assert parsed.evaluations[1].effective_multiplier == 1.1
