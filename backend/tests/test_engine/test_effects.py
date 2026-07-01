from src.engine.effects import calculate_base_effects
from src.engine.types import ActionType
from tests.test_engine._helpers import make_action, make_player, make_state


def test_military_offensive_with_target_damages_target_mil() -> None:
    state = make_state(make_player("macedonia"), make_player("atenas"))
    action = make_action(
        "macedonia",
        ActionType.MILITARY_OFFENSIVE,
        target_id="atenas",
        mil=3,
    )
    effects = calculate_base_effects(action, state)
    assert effects.resource_changes["atenas"]["MIL"] == -6  # 3 * 2
    assert effects.tension_delta == 9 + 1  # min(9, 12) + ambiguous posture


def test_military_offensive_without_target_only_raises_tension() -> None:
    state = make_state(make_player("esparta"))
    action = make_action("esparta", ActionType.MILITARY_OFFENSIVE, mil=2)
    effects = calculate_base_effects(action, state)
    assert effects.resource_changes == {}
    assert effects.tension_delta == 6 + 1  # 2*3 + ambiguous


def test_diplomatic_proposal_lowers_tension() -> None:
    state = make_state(make_player("corinto"))
    action = make_action("corinto", ActionType.DIPLOMATIC_PROPOSAL, dip=3, posture="cooperative")
    effects = calculate_base_effects(action, state)
    assert effects.tension_delta == -min(3 * 2, 8) - 1  # cooperative -1
    assert effects.resource_changes == {}


def test_economic_sanction_damages_target_eco() -> None:
    state = make_state(make_player("atenas"), make_player("corinto"))
    action = make_action(
        "atenas", ActionType.ECONOMIC_SANCTION, target_id="corinto", eco=4
    )
    effects = calculate_base_effects(action, state)
    assert effects.resource_changes["corinto"]["ECO"] == -6  # int(4 * 1.5) = 6
    assert effects.tension_delta == 3 + 1  # base + ambiguous


def test_pure_intel_has_no_resource_changes_in_phase_2() -> None:
    state = make_state(make_player("persia"), make_player("atenas"))
    action = make_action(
        "persia", ActionType.INTEL_ESPIONAGE, target_id="atenas", intel=3
    )
    effects = calculate_base_effects(action, state)
    assert effects.resource_changes == {}
