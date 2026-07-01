from src.engine.effects import calculate_base_effects
from src.engine.tension import check_thresholds
from src.engine.types import ActionType, ThresholdEvent
from tests.test_engine._helpers import make_action, make_player, make_state


def test_threshold_emergency_unlocked_when_crossing_70() -> None:
    events = check_thresholds(65, 72)
    assert ThresholdEvent.EMERGENCY_UNLOCKED in events
    assert ThresholdEvent.FINAL_TURN_TRIGGERED not in events


def test_threshold_final_turn_when_crossing_85() -> None:
    events = check_thresholds(80, 88)
    assert ThresholdEvent.FINAL_TURN_TRIGGERED in events
    # Already above 70 → emergency threshold not re-crossed.
    assert ThresholdEvent.EMERGENCY_UNLOCKED not in events


def test_threshold_emergency_and_final_when_jumping_from_low() -> None:
    events = check_thresholds(65, 90)
    assert ThresholdEvent.EMERGENCY_UNLOCKED in events
    assert ThresholdEvent.FINAL_TURN_TRIGGERED in events


def test_threshold_catastrophic_at_100() -> None:
    events = check_thresholds(90, 100)
    assert ThresholdEvent.CATASTROPHIC in events


def test_threshold_global_accord_when_dropping_to_20() -> None:
    events = check_thresholds(35, 18)
    assert ThresholdEvent.GLOBAL_ACCORD_AVAILABLE in events


def test_no_threshold_when_staying_in_band() -> None:
    assert check_thresholds(50, 55) == []


def test_posture_confrontational_adds_two_tension() -> None:
    state = make_state(make_player("macedonia"))
    a = make_action("macedonia", ActionType.GENERIC, posture="confrontational")
    effects = calculate_base_effects(a, state)
    assert effects.tension_delta == 2


def test_posture_cooperative_subtracts_one_tension() -> None:
    state = make_state(make_player("atenas"))
    a = make_action("atenas", ActionType.GENERIC, posture="cooperative")
    effects = calculate_base_effects(a, state)
    assert effects.tension_delta == -1


def test_posture_ambiguous_adds_one_tension() -> None:
    state = make_state(make_player("persia"))
    a = make_action("persia", ActionType.GENERIC, posture="ambiguous")
    effects = calculate_base_effects(a, state)
    assert effects.tension_delta == 1
