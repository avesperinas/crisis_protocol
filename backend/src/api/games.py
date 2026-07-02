"""Game lifecycle endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_ai_service, get_current_user_optional, get_session
from src.engine.objectives import evaluate_objective
from src.engine.scoring import calculate_score
from src.models import Game, Pact, Player, Turn, User
from src.schemas.api import (
    FactionView,
    FinalResultView,
    GameCreate,
    GameCreatedResponse,
    GameJoin,
    GameStateView,
    LobbySlot,
    LobbyStateView,
    MessageView,
    PactView,
    PlayerView,
    ResolvedActionView,
    ScoreboardEntry,
    ScoreBreakdownView,
    TurnView,
)
from src.scenarios import get_scenario
from src.services.ai_service import AIService
from src.services.connection_manager import manager as ws_manager
from src.services.game_service import (
    GameServiceError,
    create_game,
    join_game,
    pregenerate_briefings,
    start_game,
)
from src.services.message_service import list_visible_messages
from src.services.state_loader import load_game_history

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("", response_model=GameCreatedResponse)
async def create_game_endpoint(
    payload: GameCreate,
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> GameCreatedResponse:
    # Game language: explicit payload wins, else the creator's account locale,
    # else Spanish. One language per game (see Game.language).
    language = payload.language or (current_user.locale if current_user else "es")
    try:
        game, human = await create_game(
            session,
            scenario_id=payload.scenario_id,
            human_role_id=payload.human_role_id,
            mode=payload.mode,
            account_id=current_user.id if current_user else None,
            room_name=payload.room_name,
            async_mode=payload.async_mode,
            language=language,
        )
    except GameServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    # In solo mode: briefings are generated immediately.
    # In multiplayer mode: briefings are generated when the host calls /start.
    if payload.mode == "solo":
        await pregenerate_briefings(session, ai_service=ai_service, game_id=game.id)
        from src.config import settings

        if settings.bot_diplomacy_enabled:
            from src.services.diplomacy_service import schedule_bot_diplomacy

            schedule_bot_diplomacy(game.id, 1)
    return GameCreatedResponse(
        game_id=game.id,
        your_role_id=human.role_id,
        user_token=human.user_id or "",
        join_code=game.join_code,
        mode=game.mode,
    )


@router.post("/join", response_model=GameCreatedResponse)
async def join_game_endpoint(
    payload: GameJoin,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_optional),
) -> GameCreatedResponse:
    try:
        game, player = await join_game(
            session,
            join_code=payload.join_code,
            role_id=payload.role_id,
            account_id=current_user.id if current_user else None,
        )
    except GameServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await ws_manager.broadcast(game.id, {"type": "lobby_updated"})
    return GameCreatedResponse(
        game_id=game.id,
        your_role_id=player.role_id,
        user_token=player.user_id or "",
        join_code=game.join_code,
        mode=game.mode,
    )


@router.post("/{game_id}/start")
async def start_game_endpoint(
    game_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
) -> dict:
    try:
        await start_game(
            session, ai_service=ai_service, game_id=game_id, requester_role_id=role_id
        )
    except GameServiceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await ws_manager.broadcast(game_id, {"type": "game_started"})
    return {"ok": True}


async def _build_lobby_view(
    session: AsyncSession, game: Game, *, requester_role_id: str | None
) -> LobbyStateView:
    scenario = get_scenario(game.scenario_id, game.language)
    players = (
        (await session.execute(select(Player).where(Player.game_id == game.id))).scalars().all()
    )
    taken = {p.role_id: p for p in players}
    slots = [
        LobbySlot(
            role_id=f.id,
            role_name=f.name,
            tagline=f.tagline,
            is_taken=f.id in taken,
            is_human=f.id in taken and not taken[f.id].is_ai,
        )
        for f in scenario.factions
    ]
    return LobbyStateView(
        game_id=game.id,
        join_code=game.join_code or "",
        room_name=game.room_name,
        scenario_id=game.scenario_id,
        scenario_name=scenario.name,
        async_mode=bool(game.turn_timeout_seconds and game.turn_timeout_seconds >= 3600),
        slots=slots,
        is_started=game.status != "lobby",
        is_host=requester_role_id is not None and game.host_role_id == requester_role_id,
        connected_roles=ws_manager.connected_roles(game.id),
    )


@router.get("/by-code/{join_code}", response_model=LobbyStateView)
async def get_lobby_by_code(
    join_code: str,
    session: AsyncSession = Depends(get_session),
) -> LobbyStateView:
    """Preview a room's scenario and open slots before committing to a role —
    used by the Lobby's join-by-code faction picker, which otherwise has no way
    to know which scenario the target room actually uses."""
    game = (
        await session.execute(select(Game).where(Game.join_code == join_code.upper()))
    ).scalar_one_or_none()
    if not game:
        raise HTTPException(404, "no room with that code")
    if game.status != "lobby":
        raise HTTPException(400, "this room is no longer open")
    return await _build_lobby_view(session, game, requester_role_id=None)


@router.get("/{game_id}/lobby", response_model=LobbyStateView)
async def get_lobby_state(
    game_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_session),
) -> LobbyStateView:
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one_or_none()
    if not game:
        raise HTTPException(404, "game not found")
    return await _build_lobby_view(session, game, requester_role_id=role_id)


@router.get("/{game_id}/state", response_model=GameStateView)
async def get_game_state(
    game_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
) -> GameStateView:
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one_or_none()
    if not game:
        raise HTTPException(404, "game not found")
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    you = next((p for p in players if p.role_id == role_id), None)
    if not you:
        raise HTTPException(404, "role not in this game")
    scenario = get_scenario(game.scenario_id, game.language)
    faction_by_id = {f.id: f for f in scenario.factions}

    # Generate briefing on demand if not cached.
    if not you.briefing and not you.is_ai:
        you.briefing = await ai_service.generate_briefing(
            scenario, faction_by_id[you.role_id], game.language
        )
        await session.commit()

    current_turn = (
        await session.execute(
            select(Turn)
            .where(Turn.game_id == game_id, Turn.turn_number == game.current_turn)
        )
    ).scalar_one_or_none()
    turn_view = await _build_turn_view(session, current_turn, you, scenario) if current_turn else None

    previous_turn_view = None
    if game.current_turn > 1:
        prev = (
            await session.execute(
                select(Turn)
                .where(Turn.game_id == game_id, Turn.turn_number == game.current_turn - 1)
            )
        ).scalar_one_or_none()
        if prev:
            previous_turn_view = await _build_turn_view(session, prev, you, scenario)

    you_view = PlayerView(
        role_id=you.role_id,
        role_name=faction_by_id[you.role_id].name,
        tagline=faction_by_id[you.role_id].tagline,
        is_ai=you.is_ai,
        is_you=True,
        briefing=you.briefing,
        resources=you.resources,
        token_budget_per_turn=faction_by_id[you.role_id].token_budget_per_turn,
        public_objective_text=faction_by_id[you.role_id].public_objective.text,
        hidden_objective_text=faction_by_id[you.role_id].hidden_objective.text,
    )
    credibility_by_role = {p.role_id: p.credibility for p in players}
    factions_view = [
        FactionView(
            id=f.id,
            name=f.name,
            tagline=f.tagline,
            public_objective=f.public_objective.text,
            credibility=credibility_by_role.get(f.id, 50),
        )
        for f in scenario.factions
    ]
    role_by_uuid = {p.id: p.role_id for p in players}
    active_pacts_db = (
        (
            await session.execute(
                select(Pact).where(Pact.game_id == game_id, Pact.is_active == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )
    active_pacts: list[PactView] = []
    for p in active_pacts_db:
        # Hide secret pacts the requester is not party to.
        if p.is_secret and you.id not in (p.player_a_id, p.player_b_id):
            continue
        active_pacts.append(
            PactView(
                id=p.id,
                type=p.type,
                player_a_id=role_by_uuid.get(p.player_a_id, "?"),
                player_b_id=role_by_uuid.get(p.player_b_id, "?"),
                is_secret=p.is_secret,
                is_active=p.is_active,
                created_turn=p.created_turn,
            )
        )

    msgs = await list_visible_messages(session, game_id=game_id, viewer_role_id=role_id)
    # Map turn id → turn_number for the view.
    all_turns = (
        (await session.execute(select(Turn).where(Turn.game_id == game_id))).scalars().all()
    )
    turn_number_by_id = {t.id: t.turn_number for t in all_turns}
    messages_view: list[MessageView] = [
        MessageView(
            id=m.id,
            turn_number=turn_number_by_id.get(m.turn_id, 0),
            from_role_id=role_by_uuid.get(m.from_player_id, "?"),
            to_role_id=role_by_uuid.get(m.to_player_id, None) if m.to_player_id else None,
            content=m.content,
            is_proposal=m.is_proposal,
            proposal_type=m.proposal_type,
            proposal_status=m.proposal_status,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in msgs
    ]

    return GameStateView(
        game_id=game.id,
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        status=game.status,
        current_turn=game.current_turn,
        max_turns=game.max_turns,
        tension=game.tension,
        your_role_id=you.role_id,
        example_directive=scenario.example_directive,
        pact_type_labels=scenario.pact_type_labels,
        factions=factions_view,
        you=you_view,
        active_pacts=active_pacts,
        messages=messages_view,
        current_turn_view=turn_view,
        previous_turn_view=previous_turn_view,
    )


@router.get("/{game_id}/result", response_model=FinalResultView)
async def get_final_result(
    game_id: str, session: AsyncSession = Depends(get_session)
) -> FinalResultView:
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one_or_none()
    if not game:
        raise HTTPException(404, "game not found")
    if game.status != "finished":
        raise HTTPException(409, "game is not finished yet")
    scenario = get_scenario(game.scenario_id, game.language)
    history = await load_game_history(session, game_id)

    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )

    scoreboard: list[ScoreboardEntry] = []
    for player in players:
        faction = next(f for f in scenario.factions if f.id == player.role_id)
        breakdown = calculate_score(scenario.id, player.role_id, history)
        public_met = evaluate_objective(scenario.id, player.role_id, "public", history)
        hidden_met = evaluate_objective(scenario.id, player.role_id, "hidden", history)
        scoreboard.append(
            ScoreboardEntry(
                role_id=player.role_id,
                role_name=faction.name,
                is_human=not player.is_ai,
                score=ScoreBreakdownView(
                    objective=breakdown.objective,
                    efficiency=breakdown.efficiency,
                    capital=breakdown.capital,
                    decision_quality=breakdown.decision_quality,
                    total=breakdown.total,
                ),
                public_objective_met=public_met,
                hidden_objective_met=hidden_met,
                public_objective_text=faction.public_objective.text,
                hidden_objective_text=faction.hidden_objective.text,
            )
        )
    scoreboard.sort(key=lambda e: e.score.total, reverse=True)

    # Final narrative: last turn's narrative.
    last_turn = (
        await session.execute(
            select(Turn)
            .where(Turn.game_id == game_id, Turn.turn_number == game.max_turns)
        )
    ).scalar_one_or_none()
    return FinalResultView(
        game_id=game.id,
        scenario_id=game.scenario_id,
        scenario_name=scenario.name,
        final_tension=game.tension,
        final_narrative=last_turn.narrative if last_turn else None,
        scoreboard=scoreboard,
    )


# ----- helpers -----


async def _build_turn_view(session: AsyncSession, turn: Turn, you: Player, scenario) -> TurnView:
    from src.models import Action

    actions = (
        (await session.execute(select(Action).where(Action.turn_id == turn.id))).scalars().all()
    )
    you_submitted = any(a.player_id == you.id for a in actions)

    all_players = (
        (await session.execute(select(Player).where(Player.game_id == turn.game_id)))
        .scalars()
        .all()
    )
    human_ids = {p.id for p in all_players if not p.is_ai}
    submitted_ids = {a.player_id for a in actions}
    humans_total = len(human_ids)
    humans_submitted = len(human_ids & submitted_ids)

    intel_for_you: str | None = None
    resolved: list[ResolvedActionView] = []
    if turn.status == "finished":
        # Build resolved view: directive visible only to the actor.
        role_by_uuid = {p.id: p.role_id for p in all_players}
        for a in actions:
            actor_role = role_by_uuid[a.player_id]
            is_you = a.player_id == you.id
            effects = a.effects or {}
            resolved.append(
                ResolvedActionView(
                    role_id=actor_role,
                    posture=a.posture,  # type: ignore[arg-type]
                    directive=a.directive if is_you else None,
                    coherence_score=a.coherence_score,
                    decision_quality=a.decision_quality,
                    effective_multiplier=a.effective_multiplier,
                    action_type=effects.get("action_type"),
                    target_id=effects.get("target_id"),
                )
            )
            if is_you:
                intel_for_you = a.intel_report

    return TurnView(
        turn_number=turn.turn_number,
        max_turns=scenario.max_turns,
        status=turn.status,
        tension_at_start=turn.tension_at_start,
        tension_at_end=turn.tension_at_end,
        narrative=turn.narrative,
        intel_for_you=intel_for_you,
        your_action_submitted=you_submitted,
        humans_submitted=humans_submitted,
        humans_total=humans_total,
        resolved_actions=resolved,
    )
