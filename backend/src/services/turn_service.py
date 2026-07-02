"""Turn orchestration: collect actions → evaluate → resolve → narrative + intel → persist.

Multi-human support: resolution only fires once ALL human players in a game have
submitted their action for the current turn. Bots fill in right before resolution.

After resolution the service broadcasts {"type": "state_updated"} via WebSocket and
(if configured) schedules an asyncio task that auto-submits for any idle humans after
TURN_TIMEOUT_SECONDS.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.bot import BotDecision, decide_with_claude_or_fallback
from src.ai.parsing import EvaluatedAction
from src.engine.intel import compute_private_observations
from src.engine.resolver import resolve_turn
from src.engine.types import ActionInput, ActionType, TokenAllocation
from src.models import Action, Game, GameStatus, Player, Turn, TurnStatus
from src.schemas.api import ActionSubmission, TokenAllocationDTO
from src.scenarios import get_scenario
from src.services.ai_service import AIService
from src.services.chronicle import (
    build_chronicle,
    credibility_summary,
    format_message_lines,
    load_turn_messages,
    pact_events_for_narrative,
    pacts_summary_for_viewer,
    public_only,
    visible_to,
)
from src.services.state_loader import load_game_state

logger = logging.getLogger("crisis.turn")

# Phase C: how much a kept/broken promise moves public credibility (0–100).
# Breaking hurts far more than keeping helps — trust is slow to build.
_CREDIBILITY_KEPT_DELTA = 5
_CREDIBILITY_BROKEN_DELTA = 12


def _intel_unavailable(language: str) -> str:
    return "No new information this turn." if language == "en" else "Sin información nueva este turno."


def _auto_action_directive(language: str) -> str:
    return (
        "(time expired — automatic action)"
        if language == "en"
        else "(tiempo agotado — acción automática)"
    )


class TurnServiceError(ValueError):
    pass


async def submit_human_action(
    session: AsyncSession,
    *,
    ai_service: AIService,
    game_id: str,
    role_id: str,
    submission: ActionSubmission,
) -> tuple[bool, str]:
    """Persist the human's action. Returns (resolved, message).

    If this is the LAST human to submit in the turn, also generates bot actions and
    resolves the turn. Otherwise, broadcasts an 'action_submitted' event and waits.
    """
    game, players_by_role, current_turn = await _load_game_turn(session, game_id)
    if game.status != GameStatus.ACTIVE.value:
        raise TurnServiceError(f"game is not active (status={game.status})")
    if current_turn.status != TurnStatus.COLLECTING.value:
        raise TurnServiceError("current turn is not collecting actions")
    if role_id not in players_by_role:
        raise TurnServiceError(f"unknown role {role_id!r}")
    human_player = players_by_role[role_id]
    if human_player.is_ai:
        raise TurnServiceError(f"role {role_id!r} is an AI player, not human")

    existing = await _existing_action_player_ids(session, current_turn.id)
    if human_player.id in existing:
        raise TurnServiceError("you have already submitted an action for this turn")

    _persist_action(session, current_turn.id, human_player.id, submission)
    await session.flush()

    submitted_after = existing | {human_player.id}
    human_players = [p for p in players_by_role.values() if not p.is_ai]
    all_humans_submitted = all(p.id in submitted_after for p in human_players)

    if not all_humans_submitted:
        await session.commit()
        from src.services.connection_manager import manager
        await manager.broadcast(game_id, {"type": "action_submitted", "role_id": role_id})
        remaining = sum(1 for p in human_players if p.id not in submitted_after)
        return False, f"action submitted — waiting for {remaining} more player(s)"

    # All humans submitted: fill bots and resolve.
    scenario = get_scenario(game.scenario_id, game.language)
    bot_targets = [
        (role, player)
        for role, player in players_by_role.items()
        if player.is_ai and player.id not in submitted_after
    ]
    if bot_targets:
        bot_decisions = await _collect_bot_decisions(
            session=session,
            ai_service=ai_service,
            scenario=scenario,
            game=game,
            current_turn=current_turn,
            bot_targets=bot_targets,
            players_by_role=players_by_role,
        )
        for (_, player), decision in zip(bot_targets, bot_decisions, strict=True):
            _persist_action(session, current_turn.id, player.id, decision.submission)
            logger.info("Bot %s turn %d source=%s", player.role_id, current_turn.turn_number, decision.source)
    await session.commit()

    await _resolve_turn_full(session, ai_service, game.id)
    return True, "turn resolved"


async def _resolve_turn_full(
    session: AsyncSession, ai_service: AIService, game_id: str
) -> None:
    game, players_by_role, turn = await _load_game_turn(session, game_id)
    scenario = get_scenario(game.scenario_id, game.language)

    actions_result = (
        await session.execute(select(Action).where(Action.turn_id == turn.id))
    ).scalars().all()
    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}

    actions_block = [
        {
            "player_id": role_by_uuid[a.player_id],
            "posture": a.posture,
            "tokens": {"MIL": a.tokens_mil, "DIP": a.tokens_dip, "ECO": a.tokens_eco, "INT": a.tokens_int},
            "directive": a.directive,
        }
        for a in actions_result
    ]

    turn.status = TurnStatus.RESOLVING.value
    await session.commit()

    # Shared memory for the AI calls: public chronicle of past turns plus this
    # turn's messages (the evaluator referees with full visibility; the
    # narrative only ever sees the public channel).
    chronicle = await build_chronicle(
        session,
        game_id=game_id,
        up_to_turn_number=turn.turn_number,
        role_by_uuid=role_by_uuid,
    )
    turn_messages = await load_turn_messages(session, turn_id=turn.id)
    all_messages_block = format_message_lines(turn_messages, role_by_uuid)
    public_messages_block = format_message_lines(public_only(turn_messages), role_by_uuid)

    state = await load_game_state(session, game_id)
    active_pacts = [
        {"a": p.player_a_id, "b": p.player_b_id, "type": p.type, "is_secret": p.is_secret}
        for p in state.pacts
        if p.is_active
    ]

    eval_result = await ai_service.evaluate_turn(
        scenario=scenario,
        turn_number=turn.turn_number,
        max_turns=scenario.max_turns,
        tension_start=turn.tension_at_start,
        actions=actions_block,
        active_pacts=active_pacts,
        previous_events=chronicle,
        messages_block=all_messages_block,
    )
    evals_by_role: dict[str, EvaluatedAction] = {
        ev.player_id: ev for ev in eval_result.response.evaluations
    }
    action_inputs: list[ActionInput] = []
    for a in actions_result:
        role = role_by_uuid[a.player_id]
        ev = evals_by_role.get(role)
        action_type = ev.action_type_enum() if ev else ActionType.GENERIC
        target_id = ev.target_id if ev else None
        if target_id and not any(p.id == target_id for p in state.players):
            target_id = None
        multiplier = ev.effective_multiplier if ev else 1.0
        action_inputs.append(
            ActionInput(
                player_id=role,
                posture=a.posture,  # type: ignore[arg-type]
                tokens=TokenAllocation(
                    MIL=a.tokens_mil, DIP=a.tokens_dip, ECO=a.tokens_eco, INT=a.tokens_int
                ),
                directive=a.directive,
                action_type=action_type,
                target_id=target_id,
                coherence_multiplier=multiplier,
            )
        )

    result = resolve_turn(action_inputs, state)

    for a in actions_result:
        role = role_by_uuid[a.player_id]
        ev = evals_by_role.get(role)
        if ev:
            a.coherence_score = ev.coherence_score
            a.posture_modifier = ev.posture_modifier
            a.decision_quality = ev.decision_quality
            a.effective_multiplier = ev.effective_multiplier
            a.effects = {
                "action_type": ev.action_type,
                "target_id": ev.target_id,
                "reasoning": ev.decision_quality_reasoning,
                "promise_assessment": ev.promise_assessment,
                "promise_note": ev.promise_note,
            }

    # Phase C: kept/broken promises move public credibility. The new value
    # takes effect from the NEXT turn's diplomacy onward (this turn resolved
    # with the credibility the players had walking in).
    for role, ev in evals_by_role.items():
        player = players_by_role.get(role)
        if not player:
            continue
        if ev.promise_assessment == "kept":
            player.credibility = min(100, player.credibility + _CREDIBILITY_KEPT_DELTA)
        elif ev.promise_assessment == "broken":
            player.credibility = max(0, player.credibility - _CREDIBILITY_BROKEN_DELTA)
            logger.info(
                "Credibility hit for %s (broken promise): now %d", role, player.credibility
            )

    for role, new_resources in result.final_player_resources.items():
        player = players_by_role.get(role)
        if player:
            player.resources = dict(new_resources)

    turn.tension_at_end = result.final_tension
    turn.status = TurnStatus.FINISHED.value
    game.tension = result.final_tension

    resolved_summary = _summarise_resolved_actions(result, evals_by_role)
    # The narrative is public: secret pacts must not reach the narrator.
    public_active_pacts = [p for p in state.pacts if p.is_active and not p.is_secret]
    pacts_summary = (
        "(none)"
        if not public_active_pacts
        else "; ".join(
            f"{p.player_a_id}<->{p.player_b_id} ({p.type})" for p in public_active_pacts
        )
    )
    new_pacts, broken_pacts = pact_events_for_narrative(state.pacts, turn.turn_number)
    threshold_note = (
        ", ".join(t.value for t in result.threshold_events) if result.threshold_events else ""
    )

    narrative = await ai_service.generate_narrative(
        scenario=scenario,
        turn_number=turn.turn_number,
        max_turns=scenario.max_turns,
        tension_start=turn.tension_at_start,
        tension_end=result.final_tension,
        resolved_summary=resolved_summary,
        pacts_summary=pacts_summary,
        new_pacts=new_pacts,
        broken_pacts=broken_pacts,
        threshold_note=threshold_note,
        chronicle=chronicle,
        public_messages=public_messages_block,
        language=game.language,
    )
    turn.narrative = narrative

    # Phase D: the deterministic intel engine decides which verified facts
    # each faction learns (espionage results, caught spies, intel-share pacts,
    # passive signals by INT level). Claude writes prose around real facts.
    hidden_objectives = {f.id: f.hidden_objective.text for f in scenario.factions}

    async def _gen(a: Action) -> str:
        role = role_by_uuid[a.player_id]
        faction = next(f for f in scenario.factions if f.id == role)
        own_action = f"Posture: {a.posture}. Directive: {a.directive!r}."
        int_level = players_by_role[role].resources.get("INT", 0)
        observations = compute_private_observations(
            viewer_id=role,
            resolved_actions=result.resolved_actions,
            state=state,
            int_level=int_level,
            hidden_objectives=hidden_objectives,
        )
        try:
            return await ai_service.generate_intel(
                scenario=scenario,
                turn_number=turn.turn_number,
                role_name=faction.name,
                int_level=int_level,
                public_summary=resolved_summary[:1000],
                own_action=own_action,
                private_observations=observations or "(no new private data)",
                language=game.language,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Intel generation failed for %s: %s", role, e)
            return _intel_unavailable(game.language)

    intel_texts = await asyncio.gather(*(_gen(a) for a in actions_result))
    for a, text in zip(actions_result, intel_texts, strict=True):
        a.intel_report = text

    game_finished = turn.turn_number >= scenario.max_turns
    if game_finished:
        game.status = GameStatus.FINISHED.value
    else:
        next_turn = Turn(
            game_id=game.id,
            turn_number=turn.turn_number + 1,
            status=TurnStatus.COLLECTING.value,
            tension_at_start=result.final_tension,
        )
        session.add(next_turn)
        game.current_turn = turn.turn_number + 1

    await session.commit()

    # Notify all connected players.
    from src.services.connection_manager import manager
    await manager.broadcast(game_id, {"type": "state_updated", "turn": game.current_turn})

    if not game_finished:
        from src.config import settings

        # Bots get one optional diplomatic move at the start of the new turn
        # (message or pact proposal), generated in the background.
        if settings.bot_diplomacy_enabled:
            from src.services.diplomacy_service import schedule_bot_diplomacy

            schedule_bot_diplomacy(game_id, game.current_turn)

        # Schedule auto-submit timeout for the next turn if the game is still running.
        # Per-game timeout (set at creation, e.g. async mode = 24h) overrides the global default.
        timeout_seconds = (
            game.turn_timeout_seconds
            if game.turn_timeout_seconds is not None
            else settings.turn_timeout_seconds
        )
        if timeout_seconds > 0:
            asyncio.create_task(
                _auto_submit_timeout(game_id, game.current_turn, timeout_seconds)
            )


async def _auto_submit_timeout(game_id: str, turn_number: int, timeout_seconds: int) -> None:
    """After timeout_seconds, auto-submit a neutral action for any human who hasn't acted."""
    await asyncio.sleep(timeout_seconds)
    from src.api.deps import get_ai_service
    from src.db import async_session

    async with async_session() as session:
        try:
            game = (
                await session.execute(select(Game).where(Game.id == game_id))
            ).scalar_one_or_none()
            if not game or game.current_turn != turn_number or game.status != GameStatus.ACTIVE.value:
                return
            turn = (
                await session.execute(
                    select(Turn).where(
                        Turn.game_id == game_id, Turn.turn_number == turn_number
                    )
                )
            ).scalar_one_or_none()
            if not turn or turn.status != TurnStatus.COLLECTING.value:
                return

            players = (
                (await session.execute(select(Player).where(Player.game_id == game_id)))
                .scalars()
                .all()
            )
            players_by_role = {p.role_id: p for p in players}
            submitted_ids = await _existing_action_player_ids(session, turn.id)
            scenario = get_scenario(game.scenario_id, game.language)
            factions_by_id = {f.id: f for f in scenario.factions}

            idle_humans = [p for p in players if not p.is_ai and p.id not in submitted_ids]
            if not idle_humans:
                return

            for player in idle_humans:
                faction = factions_by_id[player.role_id]
                budget = faction.token_budget_per_turn
                per = budget // 4
                rem = budget - per * 4
                auto = ActionSubmission(
                    posture="ambiguous",
                    tokens=TokenAllocationDTO(MIL=per, DIP=per + rem, ECO=per, INT=per),
                    directive=_auto_action_directive(game.language),
                )
                _persist_action(session, turn.id, player.id, auto)
                logger.info(
                    "Auto-submitted for %s in game %s turn %d (timeout)",
                    player.role_id, game_id, turn_number,
                )

            # Fill remaining bots and resolve.
            submitted_ids = await _existing_action_player_ids(session, turn.id)
            bot_targets = [
                (role, p) for role, p in players_by_role.items()
                if p.is_ai and p.id not in submitted_ids
            ]
            ai_service = get_ai_service()
            if bot_targets:
                bot_decisions = await _collect_bot_decisions(
                    session=session,
                    ai_service=ai_service,
                    scenario=scenario,
                    game=game,
                    current_turn=turn,
                    bot_targets=bot_targets,
                    players_by_role=players_by_role,
                )
                for (_, p), decision in zip(bot_targets, bot_decisions, strict=True):
                    _persist_action(session, turn.id, p.id, decision.submission)
            await session.commit()
            await _resolve_turn_full(session, ai_service, game_id)
        except Exception as e:  # noqa: BLE001
            logger.error("Auto-submit timeout failed for game %s turn %d: %s", game_id, turn_number, e)


# ---------- helpers ----------


async def _collect_bot_decisions(
    *,
    session: AsyncSession,
    ai_service: AIService,
    scenario,
    game: Game,
    current_turn: Turn,
    bot_targets: list[tuple[str, Player]],
    players_by_role: dict[str, Player],
) -> list[BotDecision]:
    intel_by_role = await _previous_intel_by_role(
        session, game.id, current_turn.turn_number
    )
    factions_by_id = {f.id: f for f in scenario.factions}

    role_by_uuid = {p.id: p.role_id for p in players_by_role.values()}
    chronicle = await build_chronicle(
        session,
        game_id=game.id,
        up_to_turn_number=current_turn.turn_number,
        role_by_uuid=role_by_uuid,
    )
    turn_messages = await load_turn_messages(session, turn_id=current_turn.id)
    active_pacts = await _load_active_pacts(session, game.id)
    credibility_block = credibility_summary(players_by_role)

    async def _decide(role: str, player: Player) -> BotDecision:
        faction = factions_by_id[role]
        messages_block = format_message_lines(
            visible_to(turn_messages, player.id), role_by_uuid
        )
        # A bot sees public pacts plus the secret ones it is a party to.
        pacts_summary = pacts_summary_for_viewer(active_pacts, role_by_uuid, player.id)
        return await decide_with_claude_or_fallback(
            ai_service=ai_service,
            scenario=scenario,
            faction=faction,
            briefing=player.briefing,
            turn_number=current_turn.turn_number,
            max_turns=scenario.max_turns,
            tension=game.tension,
            resources=dict(player.resources),
            pacts_summary=pacts_summary,
            chronicle=chronicle,
            messages_block=messages_block,
            credibility_block=credibility_block,
            previous_intel=intel_by_role.get(role, "(no previous report)"),
            language=game.language,
        )

    results = await asyncio.gather(
        *(_decide(role, player) for role, player in bot_targets),
        return_exceptions=True,
    )
    out: list[BotDecision] = []
    for (role, player), res in zip(bot_targets, results, strict=True):
        if isinstance(res, BaseException):
            logger.warning("Bot %s raised %s — using stub.", role, res)
            from src.ai.bot import decide_stub
            faction = factions_by_id[role]
            out.append(
                decide_stub(
                    role_id=role,
                    role_name=faction.name,
                    turn_number=current_turn.turn_number,
                    token_budget=faction.token_budget_per_turn,
                    language=game.language,
                )
            )
        else:
            out.append(res)
    return out


async def _previous_intel_by_role(
    session: AsyncSession, game_id: str, current_turn_number: int
) -> dict[str, str]:
    """Each faction's intel report from the previous turn. The public narrative
    is no longer returned here — bots now receive the full chronicle instead.
    """
    if current_turn_number <= 1:
        return {}
    prev_turn = (
        await session.execute(
            select(Turn).where(Turn.game_id == game_id, Turn.turn_number == current_turn_number - 1)
        )
    ).scalar_one_or_none()
    if not prev_turn:
        return {}

    actions = (
        (await session.execute(select(Action).where(Action.turn_id == prev_turn.id))).scalars().all()
    )
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    role_by_uuid = {p.id: p.role_id for p in players}
    intel_by_role: dict[str, str] = {}
    for a in actions:
        role = role_by_uuid.get(a.player_id)
        if role and a.intel_report:
            intel_by_role[role] = a.intel_report
    return intel_by_role


async def _load_active_pacts(session: AsyncSession, game_id: str):
    from src.models import Pact

    return (
        (
            await session.execute(
                select(Pact).where(Pact.game_id == game_id, Pact.is_active == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )


async def _load_game_turn(
    session: AsyncSession, game_id: str
) -> tuple[Game, dict[str, Player], Turn]:
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one()
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    players_by_role = {p.role_id: p for p in players}
    turn = (
        await session.execute(
            select(Turn).where(Turn.game_id == game_id, Turn.turn_number == game.current_turn)
        )
    ).scalar_one()
    return game, players_by_role, turn


async def _existing_action_player_ids(session: AsyncSession, turn_id: str) -> set[str]:
    rows = (
        await session.execute(select(Action.player_id).where(Action.turn_id == turn_id))
    ).scalars().all()
    return set(rows)


def _persist_action(
    session: AsyncSession, turn_id: str, player_uuid: str, submission: ActionSubmission
) -> Action:
    action = Action(
        turn_id=turn_id,
        player_id=player_uuid,
        posture=submission.posture,
        tokens_mil=submission.tokens.MIL,
        tokens_dip=submission.tokens.DIP,
        tokens_eco=submission.tokens.ECO,
        tokens_int=submission.tokens.INT,
        directive=submission.directive,
    )
    session.add(action)
    return action


def _summarise_resolved_actions(result, evals_by_role: dict | None = None) -> str:
    chunks: list[str] = []
    for ra in result.resolved_actions:
        a = ra.action
        line = (
            f"{a.player_id} | posture={a.posture} | type={a.action_type.value}"
            + (f" | target={a.target_id}" if a.target_id else "")
            + f"\n  directive: {a.directive}"
        )
        ev = (evals_by_role or {}).get(a.player_id)
        if ev is not None and ev.promise_assessment != "none":
            # Feeds the public narrative: a kept word or a betrayal is a fact
            # the narrator may (and should) dramatize.
            line += f"\n  promise {ev.promise_assessment.upper()}: {ev.promise_note}"
        effects = ra.final_effects
        resource_changes = {
            role: {k: v for k, v in changes.items() if v != 0}
            for role, changes in effects.resource_changes.items()
            if any(v != 0 for v in changes.values())
        }
        if resource_changes:
            changes_str = "; ".join(f"{role}: {ch}" for role, ch in resource_changes.items())
            line += f"\n  resource effects: {changes_str}"
        if effects.tension_delta != 0:
            line += f"\n  tension impact: {effects.tension_delta:+d}"
        if effects.espionage_revealed:
            line += "\n  espionage revealed"
        chunks.append(line)
    return "\n\n".join(chunks)
