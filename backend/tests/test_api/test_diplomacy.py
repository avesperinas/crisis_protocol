"""Phase B tests: pending pact proposals, bot message replies and
bot-initiated diplomacy."""

import json
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.ai.parsing import (
    BotDecisionResponse,
    BotDiplomacyResponse,
    BotTokens,
    EvaluationResponse,
    PactDecisionResponse,
)
from src.api.deps import get_session, set_ai_service
from src.main import app
from src.models import Game, GameStatus, Message, Pact, Player, Turn, TurnStatus
from src.services.ai_service import TurnEvaluation
from src.services.diplomacy_service import (
    generate_bot_reply,
    run_bot_diplomacy_for_game,
)


class _FakeAI:
    def __init__(
        self,
        *,
        reply: str | None = "Consideraré vuestra oferta con atención.",
        diplomacy: BotDiplomacyResponse | None = None,
        pact_decision: PactDecisionResponse | None = None,
    ) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.reply = reply
        self.diplomacy = diplomacy
        self.pact_decision = pact_decision or PactDecisionResponse(accept=True, reason="ok")

    async def generate_briefing(self, scenario, faction, language="es") -> str:
        self.calls.append(("briefing", {"role": faction.id}))
        return f"Briefing for {faction.name}."

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
        return "Narrativa fake."

    async def generate_intel(self, **kwargs) -> str:
        return "Intel fake."

    async def decide_bot_action(self, **kwargs) -> BotDecisionResponse:
        budget = kwargs["token_budget"]
        return BotDecisionResponse(
            posture="ambiguous",
            tokens=BotTokens(DIP=budget),
            directive="ok",
        )

    async def decide_pact_response(self, **kwargs) -> PactDecisionResponse:
        self.calls.append(("pact", {"role": kwargs["faction"].id}))
        return self.pact_decision

    async def reply_to_message(self, **kwargs) -> str | None:
        self.calls.append(("reply", {"role": kwargs["faction"].id, "incoming": kwargs["incoming"]}))
        return self.reply

    async def decide_bot_diplomacy(self, **kwargs) -> BotDiplomacyResponse | None:
        self.calls.append(("diplomacy", {"role": kwargs["faction"].id}))
        return self.diplomacy


@pytest_asyncio.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    fake = _FakeAI()
    set_ai_service(fake)  # type: ignore[arg-type]
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    set_ai_service(None)  # type: ignore[arg-type]


async def _create_game(c: AsyncClient, role: str = "macedonia") -> str:
    r = await c.post(
        "/api/games", json={"scenario_id": "corinth_338", "human_role_id": role}
    )
    assert r.status_code == 200, r.text
    return r.json()["game_id"]


def _propose(c: AsyncClient, game_id: str, from_role: str, to_role: str, pact_type="alliance"):
    return c.post(
        f"/api/games/{game_id}/pacts/propose",
        params={"role_id": from_role},
        content=json.dumps({"target_role_id": to_role, "pact_type": pact_type}),
        headers={"Content-Type": "application/json"},
    )


# ----------- pending proposals (target is human) -----------


async def test_proposal_to_human_stays_pending_then_accepted(client: AsyncClient) -> None:
    game_id = await _create_game(client)  # macedonia is the human
    r = await _propose(client, game_id, "tebas", "macedonia")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["accepted"] is False
    assert body["pact_id"] is None
    message_id = body["proposal_message_id"]

    # No pact yet.
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert r.json()["active_pacts"] == []

    # Recipient accepts.
    r = await client.post(
        f"/api/games/{game_id}/pacts/proposals/{message_id}/respond",
        params={"role_id": "macedonia"},
        content=json.dumps({"accept": True}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "accepted"
    assert body["pact_id"]

    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    state = r.json()
    assert any(
        p["type"] == "alliance" and {p["player_a_id"], p["player_b_id"]} == {"tebas", "macedonia"}
        for p in state["active_pacts"]
    )
    proposal = next(m for m in state["messages"] if m["is_proposal"])
    assert proposal["proposal_status"] == "accepted"


async def test_proposal_to_human_rejected(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    message_id = (await _propose(client, game_id, "tebas", "macedonia")).json()[
        "proposal_message_id"
    ]
    r = await client.post(
        f"/api/games/{game_id}/pacts/proposals/{message_id}/respond",
        params={"role_id": "macedonia"},
        content=json.dumps({"accept": False}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    r = await client.get(f"/api/games/{game_id}/state", params={"role_id": "macedonia"})
    assert r.json()["active_pacts"] == []


async def test_only_recipient_can_respond_and_only_once(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    message_id = (await _propose(client, game_id, "tebas", "macedonia")).json()[
        "proposal_message_id"
    ]
    # Wrong responder.
    r = await client.post(
        f"/api/games/{game_id}/pacts/proposals/{message_id}/respond",
        params={"role_id": "atenas"},
        content=json.dumps({"accept": True}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 409
    # Right responder accepts…
    r = await client.post(
        f"/api/games/{game_id}/pacts/proposals/{message_id}/respond",
        params={"role_id": "macedonia"},
        content=json.dumps({"accept": True}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    # …and cannot respond twice.
    r = await client.post(
        f"/api/games/{game_id}/pacts/proposals/{message_id}/respond",
        params={"role_id": "macedonia"},
        content=json.dumps({"accept": False}),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 409


async def test_pending_proposal_blocks_duplicates(client: AsyncClient) -> None:
    game_id = await _create_game(client)
    assert (await _propose(client, game_id, "tebas", "macedonia")).status_code == 200
    r = await _propose(client, game_id, "tebas", "macedonia", pact_type="trade")
    assert r.status_code == 409


# ----------- bot replies and bot diplomacy (service level) -----------


async def _make_active_game(session: AsyncSession) -> tuple[Game, dict[str, Player], Turn]:
    game = Game(
        scenario_id="corinth_338",
        max_turns=6,
        status=GameStatus.ACTIVE.value,
        current_turn=1,
        tension=50,
    )
    session.add(game)
    await session.flush()
    players: dict[str, Player] = {}
    for role, is_ai in (("macedonia", False), ("tebas", True), ("atenas", True)):
        p = Player(
            game_id=game.id,
            role_id=role,
            is_ai=is_ai,
            briefing=f"Briefing de {role}.",
            resources={"MIL": 10, "DIP": 10, "ECO": 10, "INT": 10},
        )
        session.add(p)
        players[role] = p
    turn = Turn(
        game_id=game.id,
        turn_number=1,
        status=TurnStatus.COLLECTING.value,
        tension_at_start=50,
    )
    session.add(turn)
    await session.commit()
    return game, players, turn


async def test_generate_bot_reply_persists_message(session: AsyncSession) -> None:
    game, players, turn = await _make_active_game(session)
    incoming = Message(
        turn_id=turn.id,
        from_player_id=players["macedonia"].id,
        to_player_id=players["tebas"].id,
        content="¿Aceptarías una tregua si retiro mis tropas?",
    )
    session.add(incoming)
    await session.commit()

    fake = _FakeAI(reply="Retira tus tropas primero y hablaremos de tregua.")
    reply = await generate_bot_reply(
        session, ai_service=fake, game_id=game.id, message_id=incoming.id  # type: ignore[arg-type]
    )
    assert reply is not None
    assert reply.from_player_id == players["tebas"].id
    assert reply.to_player_id == players["macedonia"].id

    stored = (
        (await session.execute(select(Message).where(Message.turn_id == turn.id)))
        .scalars()
        .all()
    )
    assert len(stored) == 2
    assert any("Retira tus tropas" in m.content for m in stored)
    # The AI saw the incoming text.
    assert fake.calls and fake.calls[0][1]["incoming"] == incoming.content


async def test_bot_reply_ignores_public_and_bot_senders(session: AsyncSession) -> None:
    game, players, turn = await _make_active_game(session)
    public = Message(
        turn_id=turn.id,
        from_player_id=players["macedonia"].id,
        to_player_id=None,
        content="Mensaje público.",
    )
    bot_to_bot = Message(
        turn_id=turn.id,
        from_player_id=players["atenas"].id,
        to_player_id=players["tebas"].id,
        content="De bot a bot.",
    )
    session.add_all([public, bot_to_bot])
    await session.commit()

    fake = _FakeAI()
    assert await generate_bot_reply(
        session, ai_service=fake, game_id=game.id, message_id=public.id  # type: ignore[arg-type]
    ) is None
    assert await generate_bot_reply(
        session, ai_service=fake, game_id=game.id, message_id=bot_to_bot.id  # type: ignore[arg-type]
    ) is None
    assert fake.calls == []


async def test_bot_diplomacy_public_message(session: AsyncSession) -> None:
    game, players, turn = await _make_active_game(session)
    fake = _FakeAI(
        diplomacy=BotDiplomacyResponse(
            action="message_public", content="La paz exige garantías."
        )
    )
    moves = await run_bot_diplomacy_for_game(
        session, ai_service=fake, game_id=game.id, turn_number=1  # type: ignore[arg-type]
    )
    assert moves == 2  # both bots made the same (fake) move
    stored = (
        (await session.execute(select(Message).where(Message.turn_id == turn.id)))
        .scalars()
        .all()
    )
    assert len(stored) == 2
    assert all(m.to_player_id is None for m in stored)


async def test_bot_diplomacy_pact_proposal_to_human_is_pending(
    session: AsyncSession,
) -> None:
    game, players, turn = await _make_active_game(session)
    fake = _FakeAI(
        diplomacy=BotDiplomacyResponse(
            action="propose_pact", target_id="macedonia", pact_type="non_aggression"
        )
    )
    moves = await run_bot_diplomacy_for_game(
        session, ai_service=fake, game_id=game.id, turn_number=1  # type: ignore[arg-type]
    )
    # Each bot proposes to the human (different party pairs, so no duplicate block).
    assert moves == 2
    proposals = (
        (
            await session.execute(
                select(Message).where(Message.turn_id == turn.id, Message.is_proposal == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )
    assert len(proposals) == 2
    assert all(p.proposal_status == "pending" for p in proposals)
    assert all(p.to_player_id == players["macedonia"].id for p in proposals)
    # No pact yet — the human hasn't answered.
    pacts = (
        (await session.execute(select(Pact).where(Pact.game_id == game.id))).scalars().all()
    )
    assert pacts == []


async def test_bot_diplomacy_none_makes_no_moves(session: AsyncSession) -> None:
    game, _, turn = await _make_active_game(session)
    fake = _FakeAI(diplomacy=BotDiplomacyResponse(action="none"))
    moves = await run_bot_diplomacy_for_game(
        session, ai_service=fake, game_id=game.id, turn_number=1  # type: ignore[arg-type]
    )
    assert moves == 0
    stored = (
        (await session.execute(select(Message).where(Message.turn_id == turn.id)))
        .scalars()
        .all()
    )
    assert stored == []
