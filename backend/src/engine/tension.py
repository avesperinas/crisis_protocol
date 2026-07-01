"""Tension threshold detection — emits events when crossing 20, 70, 85, 100."""

from src.engine.types import ThresholdEvent

GLOBAL_ACCORD_THRESHOLD = 20
EMERGENCY_THRESHOLD = 70
FINAL_TURN_THRESHOLD = 85
CATASTROPHIC = 100


def check_thresholds(old_tension: int, new_tension: int) -> list[ThresholdEvent]:
    events: list[ThresholdEvent] = []

    # GLOBAL_ACCORD: emitted when tension *drops to or below* 20.
    if old_tension > GLOBAL_ACCORD_THRESHOLD >= new_tension:
        events.append(ThresholdEvent.GLOBAL_ACCORD_AVAILABLE)

    # Rising thresholds.
    if old_tension < EMERGENCY_THRESHOLD <= new_tension:
        events.append(ThresholdEvent.EMERGENCY_UNLOCKED)
    if old_tension < FINAL_TURN_THRESHOLD <= new_tension:
        events.append(ThresholdEvent.FINAL_TURN_TRIGGERED)
    if new_tension >= CATASTROPHIC:
        events.append(ThresholdEvent.CATASTROPHIC)

    return events
