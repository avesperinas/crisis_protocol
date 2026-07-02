"""Phase C: credibility scales diplomatic effectiveness and feeds scoring.

Note: base effects include the posture adjustment (ambiguous = +1 tension),
so a DIP=4 proposal lands at -8 + 1 = -7 tension before credibility scaling.
"""

from src.engine.resolver import resolve_turn
from src.engine.scoring import calculate_score
from src.engine.types import ActionType, GameHistory, PlayerState
from tests.test_engine._helpers import make_action, make_player, make_state


def _player_with_credibility(role_id: str, credibility: int) -> PlayerState:
    p = make_player(role_id)
    p.credibility = credibility
    return p


def test_high_credibility_amplifies_diplomacy() -> None:
    # Base -7 (see module docstring). At credibility 100 → x1.3 → int(-9.1) = -9.
    state = make_state(_player_with_credibility("atenas", 100), make_player("esparta"))
    action = make_action("atenas", ActionType.DIPLOMATIC_PROPOSAL, target_id="esparta", dip=4)
    result = resolve_turn([action], state)
    assert result.resolved_actions[0].final_effects.tension_delta == -9
    assert any("credibility" in line for line in result.log)


def test_low_credibility_dampens_diplomacy() -> None:
    # At credibility 0 → x0.7 → int(-4.9) = -4.
    state = make_state(_player_with_credibility("atenas", 0), make_player("esparta"))
    action = make_action("atenas", ActionType.DIPLOMATIC_PROPOSAL, target_id="esparta", dip=4)
    result = resolve_turn([action], state)
    assert result.resolved_actions[0].final_effects.tension_delta == -4


def test_neutral_credibility_changes_nothing() -> None:
    state = make_state(_player_with_credibility("atenas", 50), make_player("esparta"))
    action = make_action("atenas", ActionType.DIPLOMATIC_PROPOSAL, target_id="esparta", dip=4)
    result = resolve_turn([action], state)
    assert result.resolved_actions[0].final_effects.tension_delta == -7
    assert not any("credibility" in line for line in result.log)


def test_credibility_ignores_military_and_own_gains() -> None:
    # Military offensive is unaffected by low credibility; and a mediator's own
    # DIP reward is never scaled either way. The mediation targets a party not
    # involved in the attack so it succeeds.
    state = make_state(
        _player_with_credibility("atenas", 0),
        _player_with_credibility("macedonia", 0),
        make_player("esparta"),
        make_player("corinto"),
    )
    attack = make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="esparta", mil=3)
    mediation = make_action("atenas", ActionType.DIPLOMATIC_MEDIATION, target_id="corinto", dip=2)
    result = resolve_turn([attack, mediation], state)
    attack_effects = result.resolved_actions[0].final_effects
    assert attack_effects.resource_changes["esparta"]["MIL"] == -6  # untouched
    mediation_effects = result.resolved_actions[1].final_effects
    assert mediation_effects.resource_changes["atenas"]["DIP"] == 1  # own gain untouched
    assert mediation_effects.tension_delta == -4  # int((-8 + 1) * 0.7)


def test_scoring_capital_reflects_credibility() -> None:
    high = make_state(_player_with_credibility("atenas", 100))
    low = make_state(_player_with_credibility("atenas", 0))
    history_high = GameHistory(state=high, turns=[], initial_resources={})
    history_low = GameHistory(state=low, turns=[], initial_resources={})
    score_high = calculate_score("corinth_338", "atenas", history_high)
    score_low = calculate_score("corinth_338", "atenas", history_low)
    assert score_high.capital == 0.02
    assert score_low.capital == 0.0  # clamped at 0
    assert score_high.total > score_low.total
