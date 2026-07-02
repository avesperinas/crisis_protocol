import pytest

from src.ai.parsing import ParseError, parse_bot_diplomacy


def test_parse_diplomacy_none() -> None:
    parsed = parse_bot_diplomacy('{"action":"none","target_id":null,"content":""}')
    assert parsed.action == "none"


def test_parse_diplomacy_public_message() -> None:
    parsed = parse_bot_diplomacy(
        '{"action":"message_public","content":"La paz exige garantías.","reasoning":"x"}'
    )
    assert parsed.action == "message_public"
    assert "garantías" in parsed.content


def test_parse_diplomacy_private_requires_target() -> None:
    with pytest.raises(ParseError):
        parse_bot_diplomacy('{"action":"message_private","content":"hola","target_id":null}')


def test_parse_diplomacy_message_requires_content() -> None:
    with pytest.raises(ParseError):
        parse_bot_diplomacy('{"action":"message_public","content":"  "}')


def test_parse_diplomacy_pact_requires_valid_type() -> None:
    with pytest.raises(ParseError):
        parse_bot_diplomacy(
            '{"action":"propose_pact","target_id":"atenas","pact_type":"vassalage"}'
        )
    parsed = parse_bot_diplomacy(
        '{"action":"propose_pact","target_id":"atenas","pact_type":"trade","is_secret":true}'
    )
    assert parsed.pact_type == "trade"
    assert parsed.is_secret is True


def test_parse_diplomacy_handles_fences_and_prose() -> None:
    text = 'Here is my move:\n```json\n{"action":"none"}\n```'
    assert parse_bot_diplomacy(text).action == "none"


def test_parse_diplomacy_invalid_action_raises() -> None:
    with pytest.raises(ParseError):
        parse_bot_diplomacy('{"action":"declare_war","target_id":"atenas"}')
