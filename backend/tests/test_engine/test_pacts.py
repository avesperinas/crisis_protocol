from src.engine.effects import calculate_base_effects
from src.engine.pacts import apply_pact_modifiers, apply_trade_flows
from src.engine.types import ActionType
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state


def test_alliance_bonus_when_partners_target_same_player() -> None:
    pact = make_pact("macedonia", "tebas", "alliance")
    state = make_state(
        make_player("macedonia"), make_player("tebas"), make_player("atenas"), pacts=[pact]
    )
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
        make_action("tebas", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
    ]
    effects = [calculate_base_effects(a, state) for a in actions]
    log = apply_pact_modifiers(actions, effects, state)
    # Macedonia base: -4, with +15%: int(-4*1.15) = -4 (int rounds toward 0). Bump magnitude.
    # Use larger numbers to see effect distinctly:
    # Re-run with mil=4 -> base -8, -8 * 1.15 = -9.2 -> int -9
    assert any("alliance" in entry for entry in log)


def test_alliance_bonus_actually_scales_target_damage() -> None:
    pact = make_pact("macedonia", "tebas", "alliance")
    state = make_state(
        make_player("macedonia"), make_player("tebas"), make_player("atenas"), pacts=[pact]
    )
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=5),
        make_action("tebas", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
    ]
    effects = [calculate_base_effects(a, state) for a in actions]
    base = effects[0].resource_changes["atenas"]["MIL"]
    apply_pact_modifiers(actions, effects, state)
    boosted = effects[0].resource_changes["atenas"]["MIL"]
    assert boosted < base  # more negative = more damage (boosted)


def test_non_aggression_reduces_offensive_between_members() -> None:
    pact = make_pact("atenas", "macedonia", "non_aggression")
    state = make_state(make_player("atenas"), make_player("macedonia"), pacts=[pact])
    actions = [
        make_action("atenas", ActionType.MILITARY_OFFENSIVE, target_id="macedonia", mil=5),
    ]
    effects = [calculate_base_effects(a, state) for a in actions]
    base = effects[0].resource_changes["macedonia"]["MIL"]
    log = apply_pact_modifiers(actions, effects, state)
    reduced = effects[0].resource_changes["macedonia"]["MIL"]
    assert reduced > base  # less negative = reduced damage
    assert int(base * 0.70) == reduced
    assert any("non-aggression" in entry for entry in log)


def test_trade_pact_flow_exchanges_resources() -> None:
    pact = make_pact("atenas", "corinto", "trade")  # defaults: a_gives ECO 1, b_gives DIP 1
    state = make_state(make_player("atenas"), make_player("corinto"), pacts=[pact])
    flows, log = apply_trade_flows(state)
    assert flows == {
        "atenas": {"ECO": -1, "DIP": 1},
        "corinto": {"ECO": 1, "DIP": -1},
    }
    assert log  # at least one entry


def test_trade_pact_respects_custom_terms() -> None:
    pact = make_pact(
        "atenas",
        "persia",
        "trade",
        is_secret=True,
        terms={"a_gives": {"INT": 2}, "b_gives": {"ECO": 3}},
    )
    state = make_state(make_player("atenas"), make_player("persia"), pacts=[pact])
    flows, _ = apply_trade_flows(state)
    assert flows["atenas"]["INT"] == -2
    assert flows["atenas"]["ECO"] == 3
    assert flows["persia"]["INT"] == 2
    assert flows["persia"]["ECO"] == -3
