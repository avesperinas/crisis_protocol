"""Aggregate stats and game history for a user's profile page.

Reuses the existing scoring engine (src.engine.scoring, src.engine.objectives)
instead of recomputing anything — a profile is just a different view over the
same data already shown on the Resolution scoreboard.
"""

from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.objectives import evaluate_objective
from src.engine.scoring import calculate_score
from src.models import Action, Game, Player
from src.scenarios import get_scenario
from src.services.state_loader import load_game_history


@dataclass
class GameHistoryEntry:
    game_id: str
    scenario_id: str
    scenario_name: str
    role_id: str
    role_name: str
    finished_at: str | None
    score_total: int
    rank: int
    player_count: int
    public_objective_met: bool
    hidden_objective_met: bool


@dataclass
class UserStats:
    games_played: int
    wins: int
    favorite_scenario: str | None
    favorite_faction: str | None
    avg_decision_quality: float
    avg_coherence: float
    public_objective_rate: float
    hidden_objective_rate: float


async def list_user_games(session: AsyncSession, *, user_id: str) -> list[GameHistoryEntry]:
    rows = (
        await session.execute(
            select(Player, Game)
            .join(Game, Game.id == Player.game_id)
            .where(Player.user_id == user_id, Player.is_ai == False, Game.status == "finished")  # noqa: E712
            .order_by(Game.finished_at.desc())
        )
    ).all()

    entries: list[GameHistoryEntry] = []
    for player, game in rows:
        scenario = get_scenario(game.scenario_id, game.language)
        faction = next((f for f in scenario.factions if f.id == player.role_id), None)
        if not faction:
            continue
        history = await load_game_history(session, game.id)

        all_players = (
            await session.execute(select(Player).where(Player.game_id == game.id))
        ).scalars().all()
        scored = sorted(
            (
                (p.role_id, calculate_score(scenario.id, p.role_id, history).total)
                for p in all_players
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        rank = next((i + 1 for i, (role, _) in enumerate(scored) if role == player.role_id), len(scored))
        score_total = next((score for role, score in scored if role == player.role_id), 0)

        entries.append(
            GameHistoryEntry(
                game_id=game.id,
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                role_id=player.role_id,
                role_name=faction.name,
                finished_at=game.finished_at.isoformat() if game.finished_at else None,
                score_total=score_total,
                rank=rank,
                player_count=len(all_players),
                public_objective_met=evaluate_objective(scenario.id, player.role_id, "public", history),
                hidden_objective_met=evaluate_objective(scenario.id, player.role_id, "hidden", history),
            )
        )
    return entries


async def compute_user_stats(session: AsyncSession, *, user_id: str) -> UserStats:
    games = await list_user_games(session, user_id=user_id)
    games_played = len(games)
    if games_played == 0:
        return UserStats(
            games_played=0,
            wins=0,
            favorite_scenario=None,
            favorite_faction=None,
            avg_decision_quality=0.0,
            avg_coherence=0.0,
            public_objective_rate=0.0,
            hidden_objective_rate=0.0,
        )

    wins = sum(1 for g in games if g.rank == 1)
    scenario_counts = Counter(g.scenario_name for g in games)
    faction_counts = Counter(g.role_name for g in games)
    public_rate = sum(1 for g in games if g.public_objective_met) / games_played
    hidden_rate = sum(1 for g in games if g.hidden_objective_met) / games_played

    player_ids = (
        await session.execute(select(Player.id).where(Player.user_id == user_id))
    ).scalars().all()
    action_stats = (
        await session.execute(
            select(Action.decision_quality, Action.coherence_score).where(
                Action.player_id.in_(player_ids), Action.decision_quality.is_not(None)
            )
        )
    ).all()
    avg_dq = (
        sum(dq for dq, _ in action_stats) / len(action_stats) if action_stats else 0.0
    )
    avg_coh = (
        sum(coh for _, coh in action_stats if coh is not None)
        / len([coh for _, coh in action_stats if coh is not None])
        if any(coh is not None for _, coh in action_stats)
        else 0.0
    )

    return UserStats(
        games_played=games_played,
        wins=wins,
        favorite_scenario=scenario_counts.most_common(1)[0][0] if scenario_counts else None,
        favorite_faction=faction_counts.most_common(1)[0][0] if faction_counts else None,
        avg_decision_quality=round(avg_dq, 2),
        avg_coherence=round(avg_coh, 2),
        public_objective_rate=round(public_rate, 2),
        hidden_objective_rate=round(hidden_rate, 2),
    )
