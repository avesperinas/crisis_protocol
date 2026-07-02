"""Pact lifecycle: propose, respond, break.

Anyone can propose to anyone (Phase B of v2). Proposals to a BOT are decided
synchronously by Claude (with the game chronicle and the conversation with the
proposer as context). Proposals to a HUMAN stay pending until the recipient
responds through the respond endpoint. Pacts activate immediately on
acceptance; breaking applies cost (−1 DIP) and bumps tension (+7) right away.
"""

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, GameStatus, Message, Pact, Player
from src.scenarios import get_scenario
from src.services.ai_service import AIService

logger = logging.getLogger("crisis.pact")

PactType = Literal["alliance", "non_aggression", "trade", "intel_share"]
ProposalStatus = Literal["accepted", "rejected", "pending"]


def _pact_reply_note(language: str, faction_name: str, *, accepted: bool, reason: str) -> str:
    """The bot's public reply appended to a proposal message, in the game language."""
    reason = reason or ("(no reason)" if language == "en" else "(sin motivo)")
    if language == "en":
        verb = "accepted" if accepted else "rejected"
        return f"Reply from {faction_name}: {verb}. Reason: {reason}"
    verb = "aceptado" if accepted else "rechazado"
    return f"Respuesta de {faction_name}: {verb}. Motivo: {reason}"


class PactServiceError(ValueError):
    pass


@dataclass(frozen=True)
class ProposalResult:
    status: ProposalStatus
    reason: str
    pact_id: str | None
    proposal_message_id: str

    @property
    def accepted(self) -> bool:
        return self.status == "accepted"


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
    """Propose a pact. Bot targets decide synchronously via Claude; human
    targets get a pending proposal they resolve later via respond_to_proposal.
    """

    if pact_type not in ("alliance", "non_aggression", "trade", "intel_share"):
        raise PactServiceError(f"unsupported pact type: {pact_type!r}")

    game, players_by_role = await _load_basics(session, game_id)
    if proposer_role_id == target_role_id:
        raise PactServiceError("cannot propose a pact to yourself")
    if proposer_role_id not in players_by_role or target_role_id not in players_by_role:
        raise PactServiceError("unknown role(s)")
    proposer = players_by_role[proposer_role_id]
    target = players_by_role[target_role_id]

    # Reject duplicates: an active pact of any type between these two parties,
    # or a proposal still awaiting the recipient's answer.
    existing_active = await _active_pact_between(session, game_id, proposer.id, target.id)
    if existing_active:
        raise PactServiceError(
            f"there is already an active pact ({existing_active.type}) between these parties"
        )
    if await _pending_proposal_between(session, game_id, proposer.id, target.id):
        raise PactServiceError("there is already a pending proposal between these parties")

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
        content=_proposal_content(pact_type, terms, is_secret, game.language),
        is_proposal=True,
        proposal_type=pact_type,
        proposal_status="pending",
        proposal_is_secret=is_secret,
        proposal_terms=terms,
    )
    session.add(proposal)
    await session.flush()

    if not target.is_ai:
        # Human recipient: leave the proposal pending and notify them.
        await session.commit()
        from src.services.connection_manager import manager

        await manager.broadcast(
            game_id,
            {"type": "pact_proposal", "to_role_id": target_role_id, "from_role_id": proposer_role_id},
        )
        return ProposalResult(
            status="pending",
            reason="",
            pact_id=None,
            proposal_message_id=proposal.id,
        )

    # Bot recipient: ask Claude synchronously, with history and conversation.
    scenario = get_scenario(game.scenario_id, game.language)
    target_faction = next(f for f in scenario.factions if f.id == target_role_id)
    proposer_faction = next(f for f in scenario.factions if f.id == proposer_role_id)
    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}
    pacts_summary = await _summarise_active_pacts(session, game_id, players_by_role)

    from src.services.chronicle import build_chronicle

    chronicle = await build_chronicle(
        session,
        game_id=game_id,
        up_to_turn_number=game.current_turn,
        role_by_uuid=role_by_uuid,
    )
    thread_block = await _thread_between(session, game_id, proposer.id, target.id, role_by_uuid)

    decision = await ai_service.decide_pact_response(
        scenario=scenario,
        faction=target_faction,
        briefing=target.briefing or "(no briefing available)",
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
        chronicle=chronicle,
        thread_block=thread_block,
        language=game.language,
    )

    if not decision.accept:
        _finalize_proposal(
            proposal, game.language, target_faction.name, accepted=False, reason=decision.reason
        )
        await session.commit()
        return ProposalResult(
            status="rejected",
            reason=decision.reason,
            pact_id=None,
            proposal_message_id=proposal.id,
        )

    pact = _create_pact_from_proposal(session, game, proposal, proposer, target)
    _finalize_proposal(
        proposal, game.language, target_faction.name, accepted=True, reason=decision.reason
    )
    await session.commit()
    return ProposalResult(
        status="accepted",
        reason=decision.reason,
        pact_id=pact.id,
        proposal_message_id=proposal.id,
    )


async def respond_to_proposal(
    session: AsyncSession,
    *,
    game_id: str,
    responder_role_id: str,
    message_id: str,
    accept: bool,
) -> ProposalResult:
    """A human recipient accepts or rejects a pending pact proposal."""
    game, players_by_role = await _load_basics(session, game_id)
    if game.status != GameStatus.ACTIVE.value:
        raise PactServiceError(f"game is not active (status={game.status})")
    if responder_role_id not in players_by_role:
        raise PactServiceError(f"unknown role {responder_role_id!r}")
    responder = players_by_role[responder_role_id]

    from src.models import Turn

    proposal = (
        await session.execute(
            select(Message)
            .join(Turn, Message.turn_id == Turn.id)
            .where(Message.id == message_id, Turn.game_id == game_id)
        )
    ).scalar_one_or_none()
    if not proposal or not proposal.is_proposal:
        raise PactServiceError("proposal not found in this game")
    if proposal.proposal_status != "pending":
        raise PactServiceError(f"proposal is already {proposal.proposal_status}")
    if proposal.to_player_id != responder.id:
        raise PactServiceError("you are not the recipient of this proposal")

    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}
    proposer_role = role_by_uuid.get(proposal.from_player_id)
    proposer = players_by_role.get(proposer_role) if proposer_role else None
    if proposer is None:
        raise PactServiceError("proposer no longer in game")

    scenario = get_scenario(game.scenario_id, game.language)
    responder_faction = next(f for f in scenario.factions if f.id == responder_role_id)

    pact_id: str | None = None
    if accept:
        existing_active = await _active_pact_between(session, game_id, proposer.id, responder.id)
        if existing_active:
            raise PactServiceError(
                f"there is already an active pact ({existing_active.type}) between these parties"
            )
        pact = _create_pact_from_proposal(session, game, proposal, proposer, responder)
        await session.flush()
        pact_id = pact.id

    _finalize_proposal(
        proposal, game.language, responder_faction.name, accepted=accept, reason=""
    )
    await session.commit()

    from src.services.connection_manager import manager

    await manager.broadcast(
        game_id,
        {
            "type": "pact_proposal_resolved",
            "accepted": accept,
            "from_role_id": proposer_role,
            "to_role_id": responder_role_id,
        },
    )
    return ProposalResult(
        status="accepted" if accept else "rejected",
        reason="",
        pact_id=pact_id,
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


def _create_pact_from_proposal(
    session: AsyncSession, game: Game, proposal: Message, proposer: Player, target: Player
) -> Pact:
    pact = Pact(
        game_id=game.id,
        type=proposal.proposal_type or "alliance",
        player_a_id=proposer.id,
        player_b_id=target.id,
        is_secret=proposal.proposal_is_secret,
        is_active=True,
        created_turn=game.current_turn,
        terms=proposal.proposal_terms,
    )
    session.add(pact)
    return pact


def _finalize_proposal(
    proposal: Message, language: str, responder_name: str, *, accepted: bool, reason: str
) -> None:
    proposal.proposal_status = "accepted" if accepted else "rejected"
    proposal.content = (
        f"{proposal.content}\n\n"
        + _pact_reply_note(language, responder_name, accepted=accepted, reason=reason)
    )


async def _thread_between(
    session: AsyncSession,
    game_id: str,
    a_uuid: str,
    b_uuid: str,
    role_by_uuid: dict[str, str],
) -> str:
    """The bilateral private conversation between two players over the whole
    game, formatted for a prompt.
    """
    from sqlalchemy import and_, or_

    from src.models import Turn
    from src.services.chronicle import format_message_lines

    messages = (
        (
            await session.execute(
                select(Message)
                .join(Turn, Message.turn_id == Turn.id)
                .where(
                    Turn.game_id == game_id,
                    or_(
                        and_(Message.from_player_id == a_uuid, Message.to_player_id == b_uuid),
                        and_(Message.from_player_id == b_uuid, Message.to_player_id == a_uuid),
                    ),
                )
                .order_by(Message.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    if not messages:
        return "(no messages exchanged)"
    return format_message_lines(list(messages), role_by_uuid)


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


async def _pending_proposal_between(
    session: AsyncSession, game_id: str, a_id: str, b_id: str
) -> bool:
    from sqlalchemy import and_, or_

    from src.models import Turn

    pending = (
        await session.execute(
            select(Message.id)
            .join(Turn, Message.turn_id == Turn.id)
            .where(
                Turn.game_id == game_id,
                Message.is_proposal == True,  # noqa: E712
                Message.proposal_status == "pending",
                or_(
                    and_(Message.from_player_id == a_id, Message.to_player_id == b_id),
                    and_(Message.from_player_id == b_id, Message.to_player_id == a_id),
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    return pending is not None


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
        return "(none)"
    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}
    return "; ".join(
        f"{role_by_uuid.get(p.player_a_id, '?')}<->{role_by_uuid.get(p.player_b_id, '?')} ({p.type})"
        for p in pacts
    )


def _build_terms(pact_type: str, custom_terms: dict | None) -> dict | None:
    if pact_type == "trade":
        return custom_terms or {"a_gives": {"ECO": 1}, "b_gives": {"DIP": 1}}
    return None


def _proposal_content(
    pact_type: str, terms: dict | None, is_secret: bool, language: str = "es"
) -> str:
    if language == "en":
        base = f"Pact proposal: {pact_type}"
        if is_secret:
            base += " (secret)"
        if terms:
            base += f" — terms: {_terms_text(pact_type, terms)}"
        return base
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
