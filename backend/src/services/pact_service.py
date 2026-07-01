"""Pact lifecycle: propose (human → bot), break (human).

Phase 6 keeps the surface small: only the human initiates. Bot decides via
Claude synchronously when the human proposes. Pacts activate immediately on
acceptance; breaking applies cost (−1 DIP) and bumps tension (+7) right away.
"""

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, Message, Pact, Player
from src.scenarios import get_scenario
from src.services.ai_service import AIService

logger = logging.getLogger("crisis.pact")

PactType = Literal["alliance", "non_aggression", "trade", "intel_share"]


class PactServiceError(ValueError):
    pass


@dataclass(frozen=True)
class ProposalResult:
    accepted: bool
    reason: str
    pact_id: str | None
    proposal_message_id: str


async def propose_pact(
    session: AsyncSession,
    *,
    ai_service: AIService,
    game_id: str,
    proposer_role_id: str,
    target_role_id: str,
    pact_type: PactType,
    is_secret: bool = False,
    custom_terms: dict | None = None,
) -> ProposalResult:
    """Human proposes a pact to a bot. We synchronously ask the bot to decide.
    On acceptance we create the Pact; on rejection we just persist a Message
    with proposal_status='rejected'."""

    if pact_type not in ("alliance", "non_aggression", "trade", "intel_share"):
        raise PactServiceError(f"unsupported pact type: {pact_type!r}")

    game, players_by_role = await _load_basics(session, game_id)
    if proposer_role_id == target_role_id:
        raise PactServiceError("cannot propose a pact to yourself")
    if proposer_role_id not in players_by_role or target_role_id not in players_by_role:
        raise PactServiceError("unknown role(s)")
    proposer = players_by_role[proposer_role_id]
    target = players_by_role[target_role_id]
    if not target.is_ai:
        raise PactServiceError("only bot-targeted proposals are supported in Phase 6")

    # Reject duplicates: an active pact of any type between these two parties.
    existing_active = await _active_pact_between(session, game_id, proposer.id, target.id)
    if existing_active:
        raise PactServiceError(
            f"there is already an active pact ({existing_active.type}) between these parties"
        )

    terms = _build_terms(pact_type, custom_terms)

    # Determine the current turn id for the Message FK.
    from src.models import Turn

    current_turn = (
        await session.execute(
            select(Turn)
            .where(Turn.game_id == game_id, Turn.turn_number == game.current_turn)
        )
    ).scalar_one()

    proposal = Message(
        turn_id=current_turn.id,
        from_player_id=proposer.id,
        to_player_id=target.id,
        content=_proposal_content(pact_type, terms, is_secret),
        is_proposal=True,
        proposal_type=pact_type,
        proposal_status="pending",
    )
    session.add(proposal)
    await session.flush()

    # Ask the bot.
    scenario = get_scenario(game.scenario_id)
    target_faction = next(f for f in scenario.factions if f.id == target_role_id)
    proposer_faction = next(f for f in scenario.factions if f.id == proposer_role_id)
    pacts_summary = await _summarise_active_pacts(session, game_id, players_by_role)

    decision = await ai_service.decide_pact_response(
        scenario=scenario,
        faction=target_faction,
        briefing=target.briefing or "(sin briefing disponible)",
        proposer_role_id=proposer_role_id,
        proposer_name=proposer_faction.name,
        pact_type=pact_type,
        is_secret=is_secret,
        terms_text=_terms_text(pact_type, terms),
        turn_number=game.current_turn,
        max_turns=game.max_turns,
        tension=game.tension,
        resources=dict(target.resources),
        pacts_summary=pacts_summary,
    )

    if not decision.accept:
        proposal.proposal_status = "rejected"
        proposal.content = (
            f"{proposal.content}\n\nRespuesta de {target_faction.name}: rechazado. "
            f"Motivo: {decision.reason or '(sin motivo)'}"
        )
        await session.commit()
        return ProposalResult(
            accepted=False,
            reason=decision.reason,
            pact_id=None,
            proposal_message_id=proposal.id,
        )

    # Accepted: create the Pact, mark proposal accepted.
    pact = Pact(
        game_id=game_id,
        type=pact_type,
        player_a_id=proposer.id,
        player_b_id=target.id,
        is_secret=is_secret,
        is_active=True,
        created_turn=game.current_turn,
        terms=terms,
    )
    session.add(pact)
    proposal.proposal_status = "accepted"
    proposal.content = (
        f"{proposal.content}\n\nRespuesta de {target_faction.name}: aceptado. "
        f"Motivo: {decision.reason or '(sin motivo)'}"
    )
    await session.commit()
    return ProposalResult(
        accepted=True,
        reason=decision.reason,
        pact_id=pact.id,
        proposal_message_id=proposal.id,
    )


async def break_pact(
    session: AsyncSession,
    *,
    game_id: str,
    breaker_role_id: str,
    pact_id: str,
) -> Pact:
    """Mark a pact as broken. Costs 1 DIP from the breaker's pool, +7 tension."""
    game, players_by_role = await _load_basics(session, game_id)
    if breaker_role_id not in players_by_role:
        raise PactServiceError(f"unknown role {breaker_role_id!r}")
    breaker = players_by_role[breaker_role_id]

    pact = (
        await session.execute(select(Pact).where(Pact.id == pact_id, Pact.game_id == game_id))
    ).scalar_one_or_none()
    if not pact:
        raise PactServiceError("pact not found in this game")
    if not pact.is_active:
        raise PactServiceError("pact is already broken")
    if breaker.id not in (pact.player_a_id, pact.player_b_id):
        raise PactServiceError("you are not a party to this pact")

    pact.is_active = False
    pact.broken_turn = game.current_turn
    pact.broken_by_player_id = breaker.id

    breaker_resources = dict(breaker.resources)
    breaker_resources["DIP"] = max(0, breaker_resources.get("DIP", 0) - 1)
    breaker.resources = breaker_resources
    game.tension = min(100, game.tension + 7)

    await session.commit()
    return pact


# ---------- helpers ----------


async def _load_basics(
    session: AsyncSession, game_id: str
) -> tuple[Game, dict[str, Player]]:
    game = (
        await session.execute(select(Game).where(Game.id == game_id))
    ).scalar_one_or_none()
    if not game:
        raise PactServiceError("game not found")
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    return game, {p.role_id: p for p in players}


async def _active_pact_between(
    session: AsyncSession, game_id: str, a_id: str, b_id: str
) -> Pact | None:
    pacts = (
        (await session.execute(select(Pact).where(Pact.game_id == game_id, Pact.is_active == True)))  # noqa: E712
        .scalars()
        .all()
    )
    for p in pacts:
        if {p.player_a_id, p.player_b_id} == {a_id, b_id}:
            return p
    return None


async def _summarise_active_pacts(
    session: AsyncSession, game_id: str, players_by_role: dict[str, Player]
) -> str:
    pacts = (
        (await session.execute(select(Pact).where(Pact.game_id == game_id, Pact.is_active == True)))  # noqa: E712
        .scalars()
        .all()
    )
    if not pacts:
        return "(ninguno)"
    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}
    return "; ".join(
        f"{role_by_uuid.get(p.player_a_id, '?')}<->{role_by_uuid.get(p.player_b_id, '?')} ({p.type})"
        for p in pacts
    )


def _build_terms(pact_type: str, custom_terms: dict | None) -> dict | None:
    if pact_type == "trade":
        return custom_terms or {"a_gives": {"ECO": 1}, "b_gives": {"DIP": 1}}
    return None


def _proposal_content(pact_type: str, terms: dict | None, is_secret: bool) -> str:
    base = f"Propuesta de pacto: {pact_type}"
    if is_secret:
        base += " (secreto)"
    if terms:
        base += f" — términos: {_terms_text(pact_type, terms)}"
    return base


def _terms_text(pact_type: str, terms: dict | None) -> str:
    if pact_type != "trade" or not terms:
        return "—"

    def fmt(d: dict) -> str:
        return ", ".join(f"{v} {k}" for k, v in d.items() if v)

    a = fmt(terms.get("a_gives", {}))
    b = fmt(terms.get("b_gives", {}))
    return f"{a or '—'} ↔ {b or '—'}"
