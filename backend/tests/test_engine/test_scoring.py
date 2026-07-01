from src.engine.scoring import calculate_score
from src.engine.types import ActionType, GameHistory, TurnRecord
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state


def _initial(*players) -> dict[str, dict[str, int]]:
    return {p.id: dict(p.resources) for p in players}


def test_score_zero_when_no_objectives_met_and_no_spend() -> None:
    players = [make_player("macedonia"), make_player("atenas")]
    state = make_state(*players)
    history = GameHistory(state=state, turns=[], initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history)
    assert score.total == 0


def test_score_objective_component_when_both_met() -> None:
    players = [
        make_player("macedonia"),
        make_player("atenas"),
        make_player("tebas"),
        make_player("corinto"),
    ]
    pacts = [
        make_pact("macedonia", "atenas", "alliance"),
        make_pact("macedonia", "tebas", "alliance"),
        make_pact("macedonia", "corinto", "alliance"),
    ]
    state = make_state(*players, pacts=pacts)
    # No offensive against Atenas in any turn → hidden also met.
    history = GameHistory(state=state, turns=[], initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history)
    assert score.objective == 0.50  # 0.30 public + 0.20 hidden


def test_score_decision_quality_clamped() -> None:
    players = [make_player("macedonia")]
    state = make_state(*players)
    history = GameHistory(state=state, turns=[], initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history, decision_quality_0_to_0_2=0.5)
    assert score.decision_quality == 0.2  # clamped to max


def test_score_capital_rewards_active_pacts_and_penalises_breakers() -> None:
    players = [make_player("macedonia"), make_player("atenas"), make_player("tebas")]
    pacts = [
        make_pact("macedonia", "atenas", "alliance"),  # active, +0.02
        make_pact(
            "macedonia",
            "tebas",
            "non_aggression",
            is_active=False,
            broken_turn=2,
            broken_by="macedonia",  # -0.03
        ),
    ]
    state = make_state(*players, pacts=pacts)
    history = GameHistory(state=state, turns=[], initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history)
    # capital = max(0, 0.02 - 0.03) = 0
    assert score.capital == 0.0


def test_score_efficiency_rewards_low_spend_with_results() -> None:
    players = [
        make_player("macedonia"),
        make_player("atenas"),
        make_player("tebas"),
        make_player("corinto"),
    ]
    pacts = [
        make_pact("macedonia", "atenas", "alliance"),
        make_pact("macedonia", "tebas", "alliance"),
        make_pact("macedonia", "corinto", "alliance"),
    ]
    state = make_state(*players, pacts=pacts)
    # Two turns of low-cost macedonia actions
    turns = [
        TurnRecord(
            turn_number=1,
            actions=[
                make_action(
                    "macedonia",
                    ActionType.DIPLOMATIC_PROPOSAL,
                    target_id="atenas",
                    dip=2,
                )
            ],
            tension_at_start=50,
            tension_at_end=45,
        ),
        TurnRecord(
            turn_number=2,
            actions=[
                make_action(
                    "macedonia",
                    ActionType.DIPLOMATIC_PROPOSAL,
                    target_id="tebas",
                    dip=2,
                )
            ],
            tension_at_start=45,
            tension_at_end=42,
        ),
    ]
    history = GameHistory(state=state, turns=turns, initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history)
    # 4 tokens total, reference 16 → ratio 1.0; both objectives met → completion 1.0
    assert score.efficiency == 0.20
    assert score.total >= 700  # objective(500) + efficiency(200) + capital(60)


def test_score_total_capped_at_1000() -> None:
    players = [
        make_player("macedonia"),
        make_player("atenas"),
        make_player("tebas"),
        make_player("corinto"),
    ]
    pacts = [
        make_pact("macedonia", "atenas", "alliance"),
        make_pact("macedonia", "tebas", "alliance"),
        make_pact("macedonia", "corinto", "alliance"),
    ]
    state = make_state(*players, pacts=pacts)
    turns = [
        TurnRecord(
            turn_number=1,
            actions=[
                make_action(
                    "macedonia", ActionType.DIPLOMATIC_PROPOSAL, target_id="atenas", dip=2
                )
            ],
            tension_at_start=50,
            tension_at_end=45,
        )
    ]
    history = GameHistory(state=state, turns=turns, initial_resources=_initial(*players))
    score = calculate_score("corinth_338", "macedonia", history, decision_quality_0_to_0_2=0.2)
    assert score.total <= 1000
