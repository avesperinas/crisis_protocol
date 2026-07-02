"""Deterministic game chronicle: the shared memory of a game (Phase A of v2).

Built on the fly from data already persisted (turns, actions, narratives,
pacts, messages) — no schema changes, no extra AI calls. The chronicle is
injected into the evaluation, narrative and bot prompts so every AI decision
reasons with continuity instead of judging each turn in a vacuum.

The chronicle is the PUBLIC record: secret pacts are excluded because the
chronicle feeds prompts whose output reaches players. The evaluator receives
secret pacts separately through its active-pacts block.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.types import PactState
from src.models import Action, Message, Pact, Turn, TurnStatus

_DIRECTIVE_MAX = 140
_MESSAGE_MAX = 220

NO_HISTORY = "(first turn — no history yet)"
NO_MESSAGES = "(none)"


async def build_chronicle(
    session: AsyncSession,
    *,
    game_id: str,
    up_to_turn_number: int,
    role_by_uuid: dict[str, str],
) -> str:
    """Public digest of every resolved turn before `up_to_turn_number`:
    tension arc, declared actions, public pact events and the turn narrative.
    """
    turns = (
        (
            await session.execute(
                select(Turn)
                .where(
                    Turn.game_id == game_id,
                    Turn.turn_number < up_to_turn_number,
                    Turn.status == TurnStatus.FINISHED.value,
                )
                .order_by(Turn.turn_number)
            )
        )
        .scalars()
        .all()
    )
    if not turns:
        return NO_HISTORY

    turn_ids = [t.id for t in turns]
    actions = (
        (await session.execute(select(Action).where(Action.turn_id.in_(turn_ids))))
        .scalars()
        .all()
    )
    actions_by_turn: dict[str, list[Action]] = {}
    for a in actions:
        actions_by_turn.setdefault(a.turn_id, []).append(a)

    pacts = (
        (
            await session.execute(
                select(Pact).where(Pact.game_id == game_id, Pact.is_secret == False)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )

    blocks: list[str] = []
    for t in turns:
        tension_end = t.tension_at_end if t.tension_at_end is not None else t.tension_at_start
        lines = [f"TURN {t.turn_number} — tension {t.tension_at_start} → {tension_end}"]
        turn_actions = sorted(
            actions_by_turn.get(t.id, []), key=lambda a: role_by_uuid.get(a.player_id, "")
        )
        for a in turn_actions:
            role = role_by_uuid.get(a.player_id, "?")
            effects = a.effects or {}
            action_type = effects.get("action_type") or "generic"
            target = effects.get("target_id")
            head = f"  {role} [{a.posture}] {action_type}" + (f" → {target}" if target else "")
            lines.append(f"{head}: {_truncate(a.directive, _DIRECTIVE_MAX)}")
        signed = [p for p in pacts if p.created_turn == t.turn_number]
        broken = [p for p in pacts if p.broken_turn == t.turn_number]
        if signed:
            lines.append(
                "  Pacts signed: "
                + "; ".join(_pact_label(p, role_by_uuid) for p in signed)
            )
        if broken:
            lines.append(
                "  Pacts broken: "
                + "; ".join(_pact_label(p, role_by_uuid) for p in broken)
            )
        if t.narrative:
            lines.append(f"  Public narrative: {t.narrative}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


async def load_turn_messages(session: AsyncSession, *, turn_id: str) -> list[Message]:
    """All messages sent during a turn, oldest first."""
    return list(
        (
            await session.execute(
                select(Message)
                .where(Message.turn_id == turn_id)
                .order_by(Message.created_at.asc())
            )
        )
        .scalars()
        .all()
    )


def format_message_lines(messages: list[Message], role_by_uuid: dict[str, str]) -> str:
    """Prompt-ready block for a list of messages. Callers pre-filter by
    visibility: the evaluator sees everything, the narrative only public
    messages, each bot only what involves it.
    """
    if not messages:
        return NO_MESSAGES
    return "\n".join(_message_line(m, role_by_uuid) for m in messages)


def visible_to(messages: list[Message], viewer_uuid: str) -> list[Message]:
    """Messages a given player may see: public ones plus private ones they
    sent or received. Mirrors message_service.list_visible_messages.
    """
    return [
        m
        for m in messages
        if m.to_player_id is None
        or m.from_player_id == viewer_uuid
        or m.to_player_id == viewer_uuid
    ]


def public_only(messages: list[Message]) -> list[Message]:
    return [m for m in messages if m.to_player_id is None]


def pacts_summary_for_viewer(pacts, role_by_uuid: dict[str, str], viewer_uuid: str) -> str:
    """Active pacts as seen by one player: public ones plus secret ones they
    are a party to. `pacts` are ORM Pact rows (player ids are UUIDs).
    """
    visible = [
        p
        for p in pacts
        if not p.is_secret or viewer_uuid in (p.player_a_id, p.player_b_id)
    ]
    if not visible:
        return "(none)"
    return "; ".join(
        f"{role_by_uuid.get(p.player_a_id, '?')}<->{role_by_uuid.get(p.player_b_id, '?')} ({p.type})"
        + (" (secret)" if p.is_secret else "")
        for p in visible
    )


def pact_events_for_narrative(
    pacts: list[PactState], turn_number: int
) -> tuple[str, str]:
    """(new_pacts, broken_pacts) strings for the narrative prompt. Secret pacts
    are excluded on both sides: their signing is not public record, and naming
    a broken one would reveal it retroactively.
    """
    new = [p for p in pacts if p.created_turn == turn_number and not p.is_secret]
    broken = [p for p in pacts if p.broken_turn == turn_number and not p.is_secret]
    return _pact_state_lines(new), _pact_state_lines(broken)


# ---------- helpers ----------


def _pact_state_lines(pacts: list[PactState]) -> str:
    if not pacts:
        return "(none)"
    return "; ".join(f"{p.player_a_id} <-> {p.player_b_id} ({p.type})" for p in pacts)


def _pact_label(pact: Pact, role_by_uuid: dict[str, str]) -> str:
    a = role_by_uuid.get(pact.player_a_id, "?")
    b = role_by_uuid.get(pact.player_b_id, "?")
    return f"{a} <-> {b} ({pact.type})"


def _message_line(m: Message, role_by_uuid: dict[str, str]) -> str:
    sender = role_by_uuid.get(m.from_player_id, "?")
    if m.to_player_id is None:
        head = f"{sender} → ALL (public)"
    else:
        head = f"{sender} → {role_by_uuid.get(m.to_player_id, '?')} (private)"
    tag = ""
    if m.is_proposal:
        tag = f" [pact proposal: {m.proposal_type or '?'} — {m.proposal_status or 'pending'}]"
    return f"- {head}{tag}: {_truncate(m.content, _MESSAGE_MAX)}"


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
