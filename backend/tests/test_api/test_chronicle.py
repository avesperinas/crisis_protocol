"""Tests for the deterministic game chronicle (Phase A of v2)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.types import PactState
from src.models import Action, Game, Message, Pact, Player, Turn, TurnStatus
from src.services.chronicle import (
    NO_HISTORY,
    NO_MESSAGES,
    build_chronicle,
    format_message_lines,
    load_turn_messages,
    pact_events_for_narrative,
    public_only,
    visible_to,
)


async def _make_game(session: AsyncSession) -> tuple[Game, dict[str, Player]]:
    game = Game(scenario_id="corinth_338", max_turns=6, current_turn=3)
    session.add(game)
    await session.flush()
    players: dict[str, Player] = {}
    for role in ("macedonia", "atenas", "esparta"):
        p = Player(
            game_id=game.id,
            role_id=role,
            is_ai=True,
            resources={"MIL": 10, "DIP": 10, "ECO": 10, "INT": 10},
        )
        session.add(p)
        players[role] = p
    await session.flush()
    return game, players


async def _add_turn(
    session: AsyncSession,
    game: Game,
    number: int,
    *,
    status: str = TurnStatus.FINISHED.value,
    narrative: str | None = None,
) -> Turn:
    turn = Turn(
        game_id=game.id,
        turn_number=number,
        status=status,
        tension_at_start=50 + number,
        tension_at_end=55 + number,
        narrative=narrative,
    )
    session.add(turn)
    await session.flush()
    return turn


def _role_by_uuid(players: dict[str, Player]) -> dict[str, str]:
    return {p.id: p.role_id for p in players.values()}


async def test_chronicle_empty_on_first_turn(session: AsyncSession) -> None:
    game, players = await _make_game(session)
    out = await build_chronicle(
        session, game_id=game.id, up_to_turn_number=1, role_by_uuid=_role_by_uuid(players)
    )
    assert out == NO_HISTORY


async def test_chronicle_digests_past_turns(session: AsyncSession) -> None:
    game, players = await _make_game(session)
    t1 = await _add_turn(session, game, 1, narrative="Macedonia mostró músculo ante la asamblea.")
    session.add(
        Action(
            turn_id=t1.id,
            player_id=players["macedonia"].id,
            posture="confrontational",
            tokens_mil=3,
            directive="Presionar militarmente a Atenas para forzar el acuerdo.",
            effects={"action_type": "military_offensive", "target_id": "atenas"},
        )
    )
    session.add(
        Action(
            turn_id=t1.id,
            player_id=players["atenas"].id,
            posture="cooperative",
            tokens_dip=3,
            directive="Buscar mediación con Esparta.",
            effects={"action_type": "diplomatic_proposal", "target_id": "esparta"},
        )
    )
    # Public pact signed on turn 1, secret pact must never appear.
    session.add(
        Pact(
            game_id=game.id,
            type="non_aggression",
            player_a_id=players["atenas"].id,
            player_b_id=players["esparta"].id,
            created_turn=1,
        )
    )
    session.add(
        Pact(
            game_id=game.id,
            type="alliance",
            player_a_id=players["macedonia"].id,
            player_b_id=players["esparta"].id,
            is_secret=True,
            created_turn=1,
        )
    )
    # Unfinished current turn must not be included.
    await _add_turn(session, game, 2, status=TurnStatus.COLLECTING.value)
    await session.commit()

    out = await build_chronicle(
        session, game_id=game.id, up_to_turn_number=2, role_by_uuid=_role_by_uuid(players)
    )
    assert "TURN 1 — tension 51 → 56" in out
    assert "macedonia [confrontational] military_offensive → atenas" in out
    assert "atenas [cooperative] diplomatic_proposal → esparta" in out
    assert "Pacts signed: atenas <-> esparta (non_aggression)" in out
    assert "Macedonia mostró músculo" in out
    assert "alliance" not in out  # secret pact excluded
    assert "TURN 2" not in out


async def test_chronicle_truncates_long_directives(session: AsyncSession) -> None:
    game, players = await _make_game(session)
    t1 = await _add_turn(session, game, 1)
    session.add(
        Action(
            turn_id=t1.id,
            player_id=players["macedonia"].id,
            posture="ambiguous",
            directive="x" * 300,
        )
    )
    await session.commit()
    out = await build_chronicle(
        session, game_id=game.id, up_to_turn_number=2, role_by_uuid=_role_by_uuid(players)
    )
    assert "x" * 300 not in out
    assert "…" in out


async def test_message_visibility_and_formatting(session: AsyncSession) -> None:
    game, players = await _make_game(session)
    t1 = await _add_turn(session, game, 1, status=TurnStatus.COLLECTING.value)
    mac, ate, esp = players["macedonia"], players["atenas"], players["esparta"]
    session.add(
        Message(turn_id=t1.id, from_player_id=mac.id, to_player_id=None, content="Paz para todos.")
    )
    session.add(
        Message(
            turn_id=t1.id,
            from_player_id=mac.id,
            to_player_id=ate.id,
            content="Atenas: si no te alías con Esparta, te respetaré.",
        )
    )
    session.add(
        Message(
            turn_id=t1.id,
            from_player_id=ate.id,
            to_player_id=esp.id,
            content="Propuesta de pacto: non_aggression",
            is_proposal=True,
            proposal_type="non_aggression",
            proposal_status="accepted",
        )
    )
    await session.commit()

    messages = await load_turn_messages(session, turn_id=t1.id)
    assert len(messages) == 3
    role_by_uuid = _role_by_uuid(players)

    # Referee view: everything.
    full = format_message_lines(messages, role_by_uuid)
    assert "macedonia → ALL (public): Paz para todos." in full
    assert "macedonia → atenas (private)" in full
    assert "[pact proposal: non_aggression — accepted]" in full

    # Public view: only the open channel.
    pub = format_message_lines(public_only(messages), role_by_uuid)
    assert "Paz para todos." in pub
    assert "private" not in pub

    # Esparta's view: public + the proposal it received, not macedonia→atenas.
    esparta_view = format_message_lines(visible_to(messages, esp.id), role_by_uuid)
    assert "Paz para todos." in esparta_view
    assert "atenas → esparta (private)" in esparta_view
    assert "macedonia → atenas" not in esparta_view

    assert format_message_lines([], role_by_uuid) == NO_MESSAGES


def test_pact_events_for_narrative_excludes_secret() -> None:
    pacts = [
        PactState(
            id="1", type="alliance", player_a_id="macedonia", player_b_id="esparta",
            created_turn=2,
        ),
        PactState(
            id="2", type="trade", player_a_id="atenas", player_b_id="corinto",
            created_turn=2, is_secret=True,
        ),
        PactState(
            id="3", type="non_aggression", player_a_id="atenas", player_b_id="tebas",
            created_turn=1, is_active=False, broken_turn=2, broken_by_player_id="tebas",
        ),
    ]
    new_pacts, broken_pacts = pact_events_for_narrative(pacts, 2)
    assert new_pacts == "macedonia <-> esparta (alliance)"
    assert broken_pacts == "atenas <-> tebas (non_aggression)"
    # Turn without events.
    new_pacts, broken_pacts = pact_events_for_narrative(pacts, 5)
    assert new_pacts == "(none)"
    assert broken_pacts == "(none)"
