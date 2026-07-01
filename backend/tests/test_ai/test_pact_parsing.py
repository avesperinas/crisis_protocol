import pytest

from src.ai.parsing import ParseError, parse_pact_decision


def test_parse_accept_clean() -> None:
    d = parse_pact_decision('{"accept": true, "reason": "alineado"}')
    assert d.accept is True
    assert d.reason == "alineado"


def test_parse_reject_clean() -> None:
    d = parse_pact_decision('{"accept": false, "reason": "compromete mi flota"}')
    assert d.accept is False


def test_parse_with_fences() -> None:
    text = '```json\n{"accept": true}\n```'
    d = parse_pact_decision(text)
    assert d.accept is True


def test_parse_with_prose_around() -> None:
    text = 'Tras analizar la propuesta:\n{"accept": false, "reason": "X"} listo.'
    d = parse_pact_decision(text)
    assert d.accept is False


def test_parse_invalid_raises() -> None:
    with pytest.raises(ParseError):
        parse_pact_decision("not json")
