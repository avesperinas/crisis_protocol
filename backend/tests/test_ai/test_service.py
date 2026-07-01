from dataclasses import dataclass
from typing import Any

import pytest
from anthropic import APIError

from src.ai.client import Models
from src.scenarios import get_scenario
from src.services.ai_service import AIService


@dataclass
class _CallRecord:
    model: str
    system: Any
    user_message: str


class FakeClient:
    """Drop-in replacement for ClaudeClient in tests."""

    def __init__(self, response: str | Exception):
        self.response = response
        self.calls: list[_CallRecord] = []

    async def call(
        self,
        *,
        model: str,
        system: Any = None,
        user_message: str,
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ) -> str:
        self.calls.append(_CallRecord(model=model, system=system, user_message=user_message))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class _FakeAPIError(APIError):
    """Bypass APIError's elaborate constructor for tests."""

    def __init__(self, msg: str = "test error"):
        Exception.__init__(self, msg)


@pytest.fixture
def scenario():
    return get_scenario("corinth_338")


@pytest.fixture
def macedonia(scenario):
    return next(f for f in scenario.factions if f.id == "macedonia")


# ---------- briefing ----------


async def test_briefing_uses_sonnet_and_returns_text(scenario, macedonia) -> None:
    fake = FakeClient("## La Situación\nTexto generado")
    service = AIService(fake)  # type: ignore[arg-type]
    out = await service.generate_briefing(scenario, macedonia)
    assert "Situación" in out
    assert fake.calls[0].model == Models.SONNET


async def test_briefing_falls_back_on_api_error(scenario, macedonia) -> None:
    fake = FakeClient(_FakeAPIError())
    service = AIService(fake)  # type: ignore[arg-type]
    out = await service.generate_briefing(scenario, macedonia)
    assert macedonia.name in out
    assert "## La Situación" in out


# ---------- evaluation ----------


GOOD_EVAL = """{
  "evaluations": [{
    "player_id": "macedonia",
    "action_type": "military_offensive",
    "target_id": "atenas",
    "coherence_score": 0.85,
    "decision_quality": 7.5,
    "effective_multiplier": 1.05
  }]
}"""


async def test_evaluate_turn_parses_and_returns_no_fallback(scenario) -> None:
    fake = FakeClient(GOOD_EVAL)
    service = AIService(fake)  # type: ignore[arg-type]
    actions = [
        {
            "player_id": "macedonia",
            "posture": "confrontational",
            "tokens": {"MIL": 3, "DIP": 1, "ECO": 0, "INT": 1},
            "directive": "Mobilize forces toward Atenas.",
        }
    ]
    result = await service.evaluate_turn(
        scenario=scenario,
        turn_number=1,
        max_turns=4,
        tension_start=50,
        actions=actions,
    )
    assert result.used_fallback is False
    assert result.response.evaluations[0].player_id == "macedonia"
    assert fake.calls[0].model == Models.HAIKU


async def test_evaluate_turn_falls_back_on_api_error(scenario) -> None:
    fake = FakeClient(_FakeAPIError())
    service = AIService(fake)  # type: ignore[arg-type]
    actions = [
        {
            "player_id": "atenas",
            "posture": "cooperative",
            "tokens": {"MIL": 0, "DIP": 2, "ECO": 1, "INT": 1},
            "directive": "Propose mediation.",
        }
    ]
    result = await service.evaluate_turn(
        scenario=scenario,
        turn_number=1,
        max_turns=4,
        tension_start=50,
        actions=actions,
    )
    assert result.used_fallback is True
    assert len(result.response.evaluations) == 1
    assert result.response.evaluations[0].player_id == "atenas"


async def test_evaluate_turn_falls_back_on_parse_error(scenario) -> None:
    fake = FakeClient("totally not json")
    service = AIService(fake)  # type: ignore[arg-type]
    result = await service.evaluate_turn(
        scenario=scenario,
        turn_number=1,
        max_turns=4,
        tension_start=50,
        actions=[
            {
                "player_id": "corinto",
                "posture": "ambiguous",
                "tokens": {"MIL": 0, "DIP": 1, "ECO": 2, "INT": 1},
                "directive": "Mediate.",
            }
        ],
    )
    assert result.used_fallback is True
    assert result.response.evaluations[0].coherence_score == 0.7  # fallback default


# ---------- narrative ----------


async def test_narrative_uses_sonnet(scenario) -> None:
    fake = FakeClient("La sesión concluyó con tensiones renovadas.")
    service = AIService(fake)  # type: ignore[arg-type]
    out = await service.generate_narrative(
        scenario=scenario,
        turn_number=2,
        max_turns=4,
        tension_start=55,
        tension_end=62,
        resolved_summary="Macedonia presiona, Atenas resiste.",
    )
    assert "tensiones" in out
    assert fake.calls[0].model == Models.SONNET


async def test_narrative_fallback_mentions_tension(scenario) -> None:
    fake = FakeClient(_FakeAPIError())
    service = AIService(fake)  # type: ignore[arg-type]
    out = await service.generate_narrative(
        scenario=scenario,
        turn_number=3,
        max_turns=4,
        tension_start=60,
        tension_end=72,
        resolved_summary="(events)",
    )
    assert "72" in out
    assert "60" in out


# ---------- intel ----------


async def test_intel_uses_sonnet(scenario) -> None:
    fake = FakeClient("Cable interno: …")
    service = AIService(fake)  # type: ignore[arg-type]
    out = await service.generate_intel(
        scenario=scenario,
        turn_number=1,
        role_name="Persia",
        int_level=18,
        public_summary="...",
        own_action="...",
    )
    assert "Cable" in out
    assert fake.calls[0].model == Models.SONNET
