from src.engine.resolver import resolve_turn
from src.engine.types import ActionType, ThresholdEvent
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state


def test_resolver_consolidates_resource_changes_and_clamps_to_zero() -> None:
    state = make_state(
        make_player("macedonia"),
        make_player("atenas", MIL=4),  # low MIL to test clamp
    )
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=5),
    ]
    result = resolve_turn(actions, state)
    # base damage = -10, atenas starts at 4 → clamp to 0
    assert result.final_player_resources["atenas"]["MIL"] == 0


def test_resolver_resources_change_only_from_effects_not_token_spend() -> None:
    """Spending tokens does NOT directly reduce the pool. Only effects do."""
    state = make_state(make_player("esparta", MIL=10), make_player("atenas"))
    actions = [
        make_action(
            "esparta", ActionType.MILITARY_DEFENSIVE, mil=3
        ),  # purely defensive: no damage anywhere
    ]
    result = resolve_turn(actions, state)
    # Esparta still has MIL = 10 in its pool, even though it allocated 3 MIL tokens.
    assert result.final_player_resources["esparta"]["MIL"] == 10


def test_resolver_applies_tension_delta_and_detects_thresholds() -> None:
    state = make_state(make_player("macedonia"), make_player("atenas"), tension=65)
    actions = [
        # MIL=4 → tension +12, plus confrontational +2 = +14 → 79 (crosses 70)
        make_action(
            "macedonia",
            ActionType.MILITARY_OFFENSIVE,
            target_id="atenas",
            mil=4,
            posture="confrontational",
        ),
    ]
    result = resolve_turn(actions, state)
    assert result.final_tension == 79
    assert ThresholdEvent.EMERGENCY_UNLOCKED in result.threshold_events


def test_resolver_full_pipeline_with_trade_pact() -> None:
    pact = make_pact("atenas", "corinto", "trade")
    state = make_state(
        make_player("atenas", ECO=10, DIP=10),
        make_player("corinto", ECO=10, DIP=10),
        pacts=[pact],
    )
    # No actions this turn — just trade flow.
    result = resolve_turn([], state)
    # atenas gives ECO 1, gets DIP 1
    assert result.final_player_resources["atenas"] == {"MIL": 10, "DIP": 11, "ECO": 9, "INT": 10}
    assert result.final_player_resources["corinto"] == {"MIL": 10, "DIP": 9, "ECO": 11, "INT": 10}


def test_resolver_coherence_multiplier_scales_target_effects() -> None:
    state = make_state(make_player("atenas"), make_player("corinto"))
    full = make_action(
        "atenas", ActionType.ECONOMIC_SANCTION, target_id="corinto", eco=4, coherence=1.0
    )
    half = make_action(
        "atenas", ActionType.ECONOMIC_SANCTION, target_id="corinto", eco=4, coherence=0.5
    )
    res_full = resolve_turn([full], state)
    res_half = resolve_turn([half], state)
    # At full coherence: corinto ECO = 10 - 6 = 4
    # At 0.5 coherence: corinto ECO = 10 - int(6 * 0.5) = 10 - 3 = 7
    assert res_full.final_player_resources["corinto"]["ECO"] == 4
    assert res_half.final_player_resources["corinto"]["ECO"] == 7


def test_resolver_returns_resolved_action_per_input() -> None:
    state = make_state(make_player("macedonia"), make_player("atenas"))
    actions = [
        make_action("macedonia", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=2),
        make_action("atenas", ActionType.MILITARY_DEFENSIVE, mil=1),
    ]
    result = resolve_turn(actions, state)
    assert len(result.resolved_actions) == 2
    assert result.resolved_actions[0].action.player_id == "macedonia"
    assert result.resolved_actions[1].action.player_id == "atenas"
