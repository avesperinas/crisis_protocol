"""Phase C end-to-end: broken promises and broken pacts move credibility,
and the state endpoint exposes it."""

import json
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.ai.parsing import (
    BotDecisionResponse,
    BotTokens,
    EvaluationResponse,
    PactDecisionResponse,
)
from src.api.deps import get_session, set_ai_service
from src.main import app
from src.services.ai_service import TurnEvaluation


class _PromiseBreakingFakeAI:
    """Evaluation marks macedonia's action as a broken promise every turn."""

    async def generate_briefing(self, scenario, faction, language="es") -> str:
        return f"Briefing for {faction.name}."

    async def evaluate_turn(self, **kwargs) -> TurnEvaluation:
        evals = [
            {
                "player_id": a["player_id"],
                "action_type": "generic",
                "target_id": None,
                "coherence_score": 0.7,
                "decision_quality": 5.0,
                "decision_quality_reasoning": "fake",
                "effective_multiplier": 1.0,
                "promise_assessment": "broken" if a["player_id"] == "macedonia" else "none",
                "promise_note": "prometió no atacar y atacó" if a["player_id"] == "macedonia" else "",
            }
            for a in kwargs["actions"]
        ]
        return TurnEvaluation(
            response=EvaluationResponse.model_validate({"evaluations": evals}),
            used_fallback=False,
        )

    async def generate_narrative(self, **kwargs) -> str:
        # Assert the betrayal reached the narrative grounding summary.
        assert "promise BROKEN" in kwargs["resolved_summary"]
        return "Narrativa fake."

    async def generate_intel(self, **kwargs) -> str:
        return "Intel fake."

    async def decide_bot_action(self, **kwargs) -> BotDecisionResponse:
        budget = kwargs["token_budget"]
        return BotDecisionResponse(
            posture="ambiguous", tokens=BotTokens(DIP=budget), directive="ok"
        )

    async def decide_pact_response(self, **kwargs) -> PactDecisionResponse:
        return PactDecisionResponse(accept=True, reason="ok")

    async def reply_to_message(self, **kwargs) -> str | None:
        return None

    async def decide_bot_diplomacy(self, **kwargs):
        return None


@pytest_asyncio.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    set_ai_service(_PromiseBreakingFakeAI())  # type: ignore[arg-type]
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    set_ai_service(None)  # type: ignore[arg-type]


async def _create_game(c: AsyncClient) -> str:
    r = await c.post(
        "/api/games", json={"scenario_id": "corinth_338", "human_role_id": "macedonia"}
    )
    assert r.status_code == 200, r.text
    return r.json()["game_id"]


def _credibility(state: dict, role: str) -> int:
    return next(f["credibility"] for f in state["factions"] if f["id"] == role)


async def test_broken_promise_lowers_credibility(client: AsyncClient) -> None:
    game_id = await _create_game(client)

    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert _credibility(r.json(), "macedonia") == 50  # neutral start

    r = await client.post(
        f"/api/games/{game_id}/actions",
        params={"role_id": "macedonia"},
        content=json.dumps(
            {
                "posture": "confrontational",
                "tokens": {"MIL": 3, "DIP": 1, "ECO": 1, "INT": 0},
                "directive": "Atacar Atenas pese al pacto.",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["turn_resolved"] is True

    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    state = r.json()
    assert _credibility(state, "macedonia") == 38  # 50 - 12
    # Bots with "none" stay neutral.
    assert _credibility(state, "atenas") == 50


async def test_breaking_a_pact_lowers_credibility(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps({"target_role_id": "tebas", "pact_type": "alliance"}),
        headers={"Content-Type": "application/json"},
    )
    pact_id = r.json()["pact_id"]
    assert pact_id

    r = await client.post(
        f"/api/games/{game_id}/pacts/{pact_id}/break", params={"role_id": "macedonia"}
    )
    assert r.status_code == 200

    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert _credibility(r.json(), "macedonia") == 40  # 50 - 10
