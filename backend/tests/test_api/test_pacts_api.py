"""End-to-end tests for /api/games/.../pacts/* and message+state interplay."""

import json
from collections.abc import AsyncIterator
from typing import Any

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


class _PactAwareFakeAI:
    """Like the basic test fake, but the pact decision is configurable per-instance."""

    def __init__(self, pact_decision: PactDecisionResponse | None = None) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.pact_decision = pact_decision or PactDecisionResponse(
            accept=True, reason="fake-accept"
        )

    async def generate_briefing(self, scenario, faction, language="es") -> str:
        self.calls.append(("briefing", {"role": faction.id}))
        return f"## La Situación\nBriefing for {faction.name}."

    async def evaluate_turn(self, **kwargs) -> TurnEvaluation:
        self.calls.append(("evaluate", kwargs))
        evals = [
            {
                "player_id": a["player_id"],
                "action_type": "generic",
                "target_id": None,
                "coherence_score": 0.7,
                "decision_quality": 5.0,
                "decision_quality_reasoning": "fake",
                "effective_multiplier": 1.0,
            }
            for a in kwargs["actions"]
        ]
        return TurnEvaluation(
            response=EvaluationResponse.model_validate({"evaluations": evals}),
            used_fallback=False,
        )

    async def generate_narrative(self, **kwargs) -> str:
        self.calls.append(("narrative", kwargs))
        return "Narrativa fake."

    async def generate_intel(self, **kwargs) -> str:
        self.calls.append(("intel", kwargs))
        return "Intel fake."

    async def decide_bot_action(self, **kwargs) -> BotDecisionResponse:
        self.calls.append(("bot", {"role": kwargs["faction"].id}))
        budget = kwargs["token_budget"]
        return BotDecisionResponse(
            posture="ambiguous",
            tokens=BotTokens(MIL=0, DIP=budget, ECO=0, INT=0),
            directive="ok",
            reasoning="fake",
        )

    async def decide_pact_response(self, **kwargs) -> PactDecisionResponse:
        self.calls.append(("pact", {"role": kwargs["faction"].id, "type": kwargs["pact_type"]}))
        return self.pact_decision


@pytest_asyncio.fixture
async def fake_ai_accept() -> AsyncIterator[_PactAwareFakeAI]:
    fake = _PactAwareFakeAI(PactDecisionResponse(accept=True, reason="aceptado"))
    set_ai_service(fake)  # type: ignore[arg-type]
    yield fake
    set_ai_service(None)  # type: ignore[arg-type]


@pytest_asyncio.fixture
async def fake_ai_reject() -> AsyncIterator[_PactAwareFakeAI]:
    fake = _PactAwareFakeAI(PactDecisionResponse(accept=False, reason="rechazo"))
    set_ai_service(fake)  # type: ignore[arg-type]
    yield fake
    set_ai_service(None)  # type: ignore[arg-type]


@pytest_asyncio.fixture
async def client(engine, fake_ai_accept) -> AsyncIterator[AsyncClient]:
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_reject(engine, fake_ai_reject) -> AsyncIterator[AsyncClient]:
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ----------- helpers -----------


async def _create_game(c: AsyncClient, role: str = "macedonia") -> str:
    r = await c.post(
        "/api/games", json={"scenario_id": "corinth_338", "human_role_id": role}
    )
    assert r.status_code == 200, r.text
    return r.json()["game_id"]


def _action(mil=0, dip=2, eco=2, int_=1, posture="ambiguous") -> dict[str, Any]:
    return {
        "posture": posture,
        "tokens": {"MIL": mil, "DIP": dip, "ECO": eco, "INT": int_},
        "directive": "ok",
    }


# ----------- tests -----------


async def test_propose_pact_accepted_creates_active_pact(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps(
            {"target_role_id": "tebas", "pact_type": "alliance", "is_secret": False}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] is True
    assert body["pact_id"]

    # State now shows it active.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    state = r.json()
    assert any(
        p["type"] == "alliance" and {p["player_a_id"], p["player_b_id"]} == {"macedonia", "tebas"}
        for p in state["active_pacts"]
    )
    # Proposal message visible to proposer.
    proposal_msgs = [m for m in state["messages"] if m["is_proposal"]]
    assert len(proposal_msgs) == 1
    assert proposal_msgs[0]["proposal_status"] == "accepted"


async def test_propose_pact_rejected(client_reject: AsyncClient) -> None:
    game_id = await _create_game(client_reject)
    r = await client_reject.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps(
            {"target_role_id": "tebas", "pact_type": "alliance", "is_secret": False}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["accepted"] is False
    assert body["pact_id"] is None

    r = await client_reject.get(
        f"/api/games/{game_id}/state", params={"role_id": "macedonia"}
    )
    state = r.json()
    assert state["active_pacts"] == []
    proposal_msgs = [m for m in state["messages"] if m["is_proposal"]]
    assert proposal_msgs[0]["proposal_status"] == "rejected"


async def test_break_pact_applies_cost_and_tension(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps({"target_role_id": "tebas", "pact_type": "alliance"}),
        headers={"Content-Type": "application/json"},
    )
    pact_id = r.json()["pact_id"]

    # Snapshot tension before break.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    state_before = r.json()
    tension_before = state_before["tension"]
    dip_before = state_before["you"]["resources"]["DIP"]

    r = await client.post(
        f"/api/games/{game_id}/pacts/{pact_id}/break",
        params={"role_id": "macedonia"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["new_tension"] == tension_before + 7
    assert body["breaker_dip_after"] == dip_before - 1


async def test_break_unknown_pact_returns_409(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/pacts/does-not-exist/break",
        params={"role_id": "macedonia"},
    )
    assert r.status_code == 409


async def test_duplicate_active_pact_rejected(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    body = {"target_role_id": "tebas", "pact_type": "alliance"}
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    assert r.json()["accepted"] is True
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 409


async def test_send_public_message_visible_to_all_via_state(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/messages",
        params={"role_id": "macedonia"},
        content=json.dumps({"to_role_id": None, "content": "Hola a todos."}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    # Viewer macedonia (sender) sees it.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert any(m["content"] == "Hola a todos." for m in r.json()["messages"])


async def test_bilateral_message_not_visible_to_third_party(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    # Note: this is unusual — humans are macedonia in our setup, but the API accepts
    # any role_id (PoC trust). We use the API directly to test visibility.
    r = await client.post(
        f"/api/games/{game_id}/messages",
        params={"role_id": "macedonia"},
        content=json.dumps({"to_role_id": "tebas", "content": "solo tu y yo."}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    # macedonia sees it.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert any(m["content"] == "solo tu y yo." for m in r.json()["messages"])
    # tebas sees it.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "tebas"})
    assert any(m["content"] == "solo tu y yo." for m in r.json()["messages"])
    # atenas does NOT see it.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "atenas"})
    assert not any(m["content"] == "solo tu y yo." for m in r.json()["messages"])


async def test_active_alliance_affects_subsequent_turn_engine(client: AsyncClient) -> None:
    """Smoke that after creating a pact, the turn_service still resolves
    (engine sees the pact in its state)."""
    game_id = await _create_game(client)
    r = await client.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": "macedonia"},
        content=json.dumps({"target_role_id": "tebas", "pact_type": "alliance"}),
        headers={"Content-Type": "application/json"},
    )
    assert r.json()["accepted"]
    r = await client.post(
        f"/api/games/{game_id}/actions",
        params={"role_id": "macedonia"},
        content=json.dumps(_action()),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["turn_resolved"] is True
