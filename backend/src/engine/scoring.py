"""Score calculation. Four components (0..1000 total):

- Objective completion (50%): 30% public + 20% hidden.
- Resource efficiency (20%): tokens spent vs effects achieved.
- Capital diplomatic (10%): pacts held, mediations, traitor flag.
- Decision quality (20%): supplied by Claude in Phase 3 (input here, 0 in Phase 2).
"""

from dataclasses import dataclass

from src.engine.objectives import evaluate_objective
from src.engine.types import ActionType, GameHistory


@dataclass(frozen=True)
class ScoreBreakdown:
    objective: float  # 0..0.5
    efficiency: float  # 0..0.2
    capital: float  # 0..0.1
    decision_quality: float  # 0..0.2
    total: int  # 0..1000


def calculate_score(
    scenario_id: str,
    role_id: str,
    history: GameHistory,
    decision_quality_0_to_0_2: float = 0.0,
) -> ScoreBreakdown:
    objective = _objective_component(scenario_id, role_id, history)
    efficiency = _efficiency_component(role_id, history)
    capital = _capital_component(role_id, history)
    dq = max(0.0, min(0.2, decision_quality_0_to_0_2))
    raw = objective + efficiency + capital + dq
    return ScoreBreakdown(
        objective=objective,
        efficiency=efficiency,
        capital=capital,
        decision_quality=dq,
        total=int(round(raw * 1000)),
    )


def _objective_component(scenario_id: str, role_id: str, history: GameHistory) -> float:
    score = 0.0
    if evaluate_objective(scenario_id, role_id, "public", history):
        score += 0.30
    if evaluate_objective(scenario_id, role_id, "hidden", history):
        score += 0.20
    return score


def _efficiency_component(role_id: str, history: GameHistory) -> float:
    """Reward objectives-met per token spent. Token spend is approximated by the
    total tokens this player allocated across all turns.
    """
    total_tokens = 0
    for turn in history.turns:
        for action in turn.actions:
            if action.player_id == role_id:
                total_tokens += action.tokens.total()
    if total_tokens == 0:
        return 0.0
    # A reference cost (~4 tokens/turn × 4 turns = 16) yields full score when both
    # objectives are met. Less spend with same outcome → higher efficiency.
    reference = 16.0
    objective_completion = 0.0
    public = evaluate_objective(history.state.scenario_id, role_id, "public", history)
    hidden = evaluate_objective(history.state.scenario_id, role_id, "hidden", history)
    if public:
        objective_completion += 0.5
    if hidden:
        objective_completion += 0.5
    if objective_completion == 0.0:
        return 0.0
    efficiency_ratio = min(1.0, reference / total_tokens)
    return 0.2 * objective_completion * efficiency_ratio


def _capital_component(role_id: str, history: GameHistory) -> float:
    """+0.02 per active pact the player is in, -0.03 per pact broken by player,
    +0.02 per successful mediation action (no failure log entry) by this player.
    Clamped [0, 0.1].
    """
    score = 0.0
    for pact in history.state.pacts:
        if role_id not in (pact.player_a_id, pact.player_b_id):
            continue
        if pact.is_active:
            score += 0.02
        elif pact.broken_by_player_id == role_id:
            score -= 0.03

    # +0.02 per mediation action this player executed in any turn.
    for turn in history.turns:
        for action in turn.actions:
            if (
                action.player_id == role_id
                and action.action_type == ActionType.DIPLOMATIC_MEDIATION
            ):
                score += 0.02

    return max(0.0, min(0.1, score))
