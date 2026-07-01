from src.engine.effects import calculate_base_effects
from src.engine.interactions import apply_interactions
from src.engine.types import ActionType
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state


def _run_interactions(actions, state):
    effects = [calculate_base_effects(a, state) for a in actions]
    log = apply_interactions(actions, effects, state)
    return effects, log


def test_attack_reduced_when_defender_mil_at_least_50_percent() -> None:
    state = make_state(make_player("macedonia"), make_player("atenas"))
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=4),
        make_action("atenas", ActionType.MILITARY_DEFENSIVE, mil=2),  # 2 == 4*0.5
    ]
    effects, log = _run_interactions(actions, state)
    # base damage was -8, reduced to 40%: int(-8 * 0.4) = -3
    assert effects[0].resource_changes["atenas"]["MIL"] == -3
    assert any("reduced by defense" in entry for entry in log)


def test_attack_full_damage_when_defense_insufficient() -> None:
    state = make_state(make_player("macedonia"), make_player("atenas"))
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=4),
        make_action("atenas", ActionType.MILITARY_DEFENSIVE, mil=1),  # < 50% of attack
    ]
    effects, log = _run_interactions(actions, state)
    assert effects[0].resource_changes["atenas"]["MIL"] == -8
    assert not any("reduced by defense" in entry for entry in log)


def test_espionage_fails_when_counter_intel_matches() -> None:
    state = make_state(make_player("persia"), make_player("atenas"))
    actions = [
        make_action("persia", ActionType.INTEL_ESPIONAGE, target_id="atenas", intel=3),
        make_action("atenas", ActionType.INTEL_COUNTER, intel=3),
    ]
    effects, log = _run_interactions(actions, state)
    assert effects[0].espionage_revealed is True
    assert effects[0].resource_changes["persia"]["INT"] == -3
    assert any("espionage" in entry and "failed" in entry for entry in log)


def test_espionage_succeeds_when_counter_weaker() -> None:
    state = make_state(make_player("persia"), make_player("atenas"))
    actions = [
        make_action("persia", ActionType.INTEL_ESPIONAGE, target_id="atenas", intel=4),
        make_action("atenas", ActionType.INTEL_COUNTER, intel=2),
    ]
    effects, log = _run_interactions(actions, state)
    assert effects[0].espionage_revealed is False
    assert "persia" not in effects[0].resource_changes


def test_sanction_reduced_25_percent_by_trade_pact() -> None:
    pact = make_pact("atenas", "persia", "trade")
    state = make_state(
        make_player("corinto"), make_player("atenas"), make_player("persia"), pacts=[pact]
    )
    actions = [
        make_action("corinto", ActionType.ECONOMIC_SANCTION, target_id="atenas", eco=4),
    ]
    effects, log = _run_interactions(actions, state)
    # base damage -6 (int(4*1.5)); reduced to int(-6*0.75) = -4
    assert effects[0].resource_changes["atenas"]["ECO"] == -4
    assert any("trade pact" in entry for entry in log)


def test_mediation_fails_when_target_attacks_in_same_turn() -> None:
    state = make_state(
        make_player("corinto"), make_player("macedonia"), make_player("atenas")
    )
    actions = [
        # Corinto tries to mediate (target = atenas as one of the disputants)
        make_action("corinto", ActionType.DIPLOMATIC_MEDIATION, target_id="atenas", dip=3),
        # Atenas attacks macedonia in the same turn → mediation involving atenas fails
        make_action("atenas", ActionType.MILITARY_OFFENSIVE, target_id="macedonia", mil=2),
    ]
    effects, log = _run_interactions(actions, state)
    # base was -8 tension + ambiguous +1 = -7; on failure tension delta becomes +5 + 1 = +6
    assert effects[0].tension_delta == 6
    assert "corinto" not in effects[0].resource_changes or "DIP" not in effects[0].resource_changes.get("corinto", {})
    assert any("mediation" in entry and "failed" in entry for entry in log)


def test_mutual_attacks_both_take_damage() -> None:
    state = make_state(make_player("atenas"), make_player("esparta"))
    actions = [
        make_action("atenas", ActionType.MILITARY_OFFENSIVE, target_id="esparta", mil=3),
        make_action("esparta", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=3),
    ]
    effects, _ = _run_interactions(actions, state)
    assert effects[0].resource_changes["esparta"]["MIL"] == -6
    assert effects[1].resource_changes["atenas"]["MIL"] == -6


def test_two_attackers_on_same_target_damage_stacks_at_consolidation() -> None:
    # In Phase 2 we don't cap stacking damage at the interaction layer; the consolidation
    # in resolver clamps to ≥ 0 but both actions register their full delta here.
    state = make_state(
        make_player("macedonia"), make_player("tebas"), make_player("atenas")
    )
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
        make_action("tebas", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
    ]
    effects, _ = _run_interactions(actions, state)
    assert effects[0].resource_changes["atenas"]["MIL"] == -4
    assert effects[1].resource_changes["atenas"]["MIL"] == -4
