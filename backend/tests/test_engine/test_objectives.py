from src.engine.objectives import evaluate_objective
from src.engine.types import ActionType, GameHistory, TurnRecord
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state


def _initial_resources(*players) -> dict[str, dict[str, int]]:
    return {p.id: dict(p.resources) for p in players}


def test_macedonia_public_met_with_three_alliances() -> None:
    players = [
        make_player("macedonia"),
        make_player("atenas"),
        make_player("tebas"),
        make_player("corinto"),
        make_player("persia"),
    ]
    pacts = [
        make_pact("macedonia", "atenas", "alliance"),
        make_pact("macedonia", "tebas", "alliance"),
        make_pact("macedonia", "corinto", "alliance"),
        make_pact("macedonia", "persia", "alliance"),  # excluded from count
    ]
    state = make_state(*players, pacts=pacts)
    history = GameHistory(state=state, turns=[], initial_resources=_initial_resources(*players))
    assert evaluate_objective("corinth_338", "macedonia", "public", history) is True


def test_macedonia_hidden_not_met_when_macedonia_attacks_atenas() -> None:
    players = [make_player("macedonia"), make_player("atenas")]
    pacts = [make_pact("macedonia", "atenas", "alliance")]
    state = make_state(*players, pacts=pacts)
    turn = TurnRecord(
        turn_number=2,
        actions=[
            make_action(
                "macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2
            )
        ],
        tension_at_start=50,
        tension_at_end=58,
    )
    history = GameHistory(
        state=state, turns=[turn], initial_resources=_initial_resources(*players)
    )
    assert evaluate_objective("corinth_338", "macedonia", "hidden", history) is False


def test_macedonia_hidden_met_when_alliance_and_no_offensive() -> None:
    players = [make_player("macedonia"), make_player("atenas")]
    pacts = [make_pact("macedonia", "atenas", "alliance")]
    state = make_state(*players, pacts=pacts)
    turn = TurnRecord(
        turn_number=1,
        actions=[
            make_action("macedonia", ActionType.DIPLOMATIC_PROPOSAL, target_id="atenas", dip=3)
        ],
        tension_at_start=50,
        tension_at_end=44,
    )
    history = GameHistory(
        state=state, turns=[turn], initial_resources=_initial_resources(*players)
    )
    assert evaluate_objective("corinth_338", "macedonia", "hidden", history) is True


def test_atenas_public_met_when_fleet_preserved() -> None:
    players = [make_player("atenas", MIL=10)]
    state = make_state(*players)
    history = GameHistory(state=state, turns=[], initial_resources={"atenas": {"MIL": 10}})
    assert evaluate_objective("corinth_338", "atenas", "public", history) is True


def test_atenas_public_not_met_when_fleet_eroded() -> None:
    players = [make_player("atenas", MIL=5)]
    state = make_state(*players)
    history = GameHistory(state=state, turns=[], initial_resources={"atenas": {"MIL": 10}})
    assert evaluate_objective("corinth_338", "atenas", "public", history) is False


def test_atenas_hidden_met_with_active_unexposed_secret_pact_with_persia() -> None:
    players = [make_player("atenas"), make_player("persia")]
    pacts = [make_pact("atenas", "persia", "intel_share", is_secret=True, id_="secret-1")]
    state = make_state(*players, pacts=pacts)
    history = GameHistory(
        state=state, turns=[], initial_resources=_initial_resources(*players), exposed_pacts=set()
    )
    assert evaluate_objective("corinth_338", "atenas", "hidden", history) is True


def test_atenas_hidden_not_met_if_pact_exposed() -> None:
    players = [make_player("atenas"), make_player("persia")]
    pacts = [make_pact("atenas", "persia", "intel_share", is_secret=True, id_="secret-1")]
    state = make_state(*players, pacts=pacts)
    history = GameHistory(
        state=state,
        turns=[],
        initial_resources=_initial_resources(*players),
        exposed_pacts={"secret-1"},
    )
    assert evaluate_objective("corinth_338", "atenas", "hidden", history) is False


def test_persia_public_is_negation_of_macedonia_public() -> None:
    players = [make_player("macedonia"), make_player("atenas"), make_player("persia")]
    state = make_state(*players)  # no alliances
    history = GameHistory(state=state, turns=[], initial_resources=_initial_resources(*players))
    assert evaluate_objective("corinth_338", "persia", "public", history) is True
    assert evaluate_objective("corinth_338", "macedonia", "public", history) is False
