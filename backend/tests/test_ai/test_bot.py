import pytest

from src.ai.bot import decide_stub, decide_with_claude_or_fallback
from src.ai.parsing import BotDecisionResponse, BotTokens, parse_bot_decision, ParseError
from src.scenarios import get_scenario


# ---------------- parse_bot_decision ----------------


def test_parse_bot_decision_clean() -> None:
    text = """{"posture":"cooperative","tokens":{"MIL":1,"DIP":2,"ECO":1,"INT":0},"directive":"Propongo mediación.","reasoning":"…"}"""
    parsed = parse_bot_decision(text, expected_budget=4)
    assert parsed.posture == "cooperative"
    assert parsed.tokens.total() == 4


def test_parse_bot_decision_handles_fences() -> None:
    text = '```json\n{"posture":"ambiguous","tokens":{"MIL":0,"DIP":0,"ECO":0,"INT":4},"directive":"x"}\n```'
    parsed = parse_bot_decision(text, expected_budget=4)
    assert parsed.posture == "ambiguous"


def test_parse_bot_decision_rejects_budget_mismatch() -> None:
    text = '{"posture":"ambiguous","tokens":{"MIL":1,"DIP":0,"ECO":0,"INT":0},"directive":"x"}'
    with pytest.raises(ParseError):
        parse_bot_decision(text, expected_budget=5)


def test_parse_bot_decision_rejects_invalid_posture() -> None:
    text = '{"posture":"furious","tokens":{"MIL":2,"DIP":2,"ECO":0,"INT":0},"directive":"x"}'
    with pytest.raises(ParseError):
        parse_bot_decision(text, expected_budget=4)


def test_parse_bot_decision_rejects_empty_directive() -> None:
    text = '{"posture":"ambiguous","tokens":{"MIL":1,"DIP":1,"ECO":1,"INT":1},"directive":""}'
    with pytest.raises(ParseError):
        parse_bot_decision(text, expected_budget=4)


# ---------------- decide_with_claude_or_fallback ----------------


class _FakeAIServiceReturnsDecision:
    def __init__(self, decision: BotDecisionResponse):
        self.decision = decision
        self.calls = 0

    async def decide_bot_action(self, **kwargs):  # noqa: ANN003
        self.calls += 1
        return self.decision


class _FakeAIServiceReturnsNone:
    def __init__(self) -> None:
        self.calls = 0

    async def decide_bot_action(self, **kwargs):  # noqa: ANN003
        self.calls += 1
        return None


@pytest.fixture
def macedonia_faction():
    scenario = get_scenario("corinth_338")
    return next(f for f in scenario.factions if f.id == "macedonia")


@pytest.fixture
def scenario_corinth():
    return get_scenario("corinth_338")


async def test_decide_falls_back_when_briefing_missing(scenario_corinth, macedonia_faction) -> None:
    ai = _FakeAIServiceReturnsNone()
    decision = await decide_with_claude_or_fallback(
        ai_service=ai,  # type: ignore[arg-type]
        scenario=scenario_corinth,
        faction=macedonia_faction,
        briefing=None,
        turn_number=1,
        max_turns=4,
        tension=50,
        resources={"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8},
    )
    assert decision.source == "stub"
    assert ai.calls == 0  # never even tried Claude


async def test_decide_uses_claude_when_briefing_present(scenario_corinth, macedonia_faction) -> None:
    canned = BotDecisionResponse(
        posture="confrontational",
        tokens=BotTokens(MIL=3, DIP=1, ECO=1, INT=0),  # sums to 5 = macedonia budget
        directive="Movilizar fuerzas hacia el Peloponeso.",
        reasoning="Demostrar fuerza temprano.",
    )
    ai = _FakeAIServiceReturnsDecision(canned)
    decision = await decide_with_claude_or_fallback(
        ai_service=ai,  # type: ignore[arg-type]
        scenario=scenario_corinth,
        faction=macedonia_faction,
        briefing="(stub briefing text)",
        turn_number=2,
        max_turns=4,
        tension=55,
        resources={"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8},
    )
    assert decision.source == "claude"
    assert decision.submission.posture == "confrontational"
    assert ai.calls == 1


async def test_decide_falls_back_when_service_returns_none(
    scenario_corinth, macedonia_faction
) -> None:
    ai = _FakeAIServiceReturnsNone()
    decision = await decide_with_claude_or_fallback(
        ai_service=ai,  # type: ignore[arg-type]
        scenario=scenario_corinth,
        faction=macedonia_faction,
        briefing="(briefing exists but Claude failed)",
        turn_number=1,
        max_turns=4,
        tension=50,
        resources={"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8},
    )
    assert decision.source == "stub"
    assert ai.calls == 1


# ---------------- stub determinism ----------------


def test_decide_stub_respects_budget() -> None:
    bot = decide_stub(role_id="atenas", role_name="Atenas", turn_number=1, token_budget=5)
    tokens = bot.submission.tokens
    assert tokens.total() == 5
