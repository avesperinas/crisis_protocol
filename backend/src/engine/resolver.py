"""Turn resolution pipeline. Pure function over GameState + actions → TurnResult.

Order:
  1. base effects per action
  2. pairwise interactions (defense, counter-intel, sanction-vs-trade, mediation)
  3. per-action pact modifiers (alliance, non-aggression)
  4. per-action coherence multiplier (stub in Phase 2: defaults to 1.0)
  5. per-action credibility modifier on diplomatic actions (Phase C)
  6. per-turn trade pact flows
  7. consolidate resource changes (clamp to ≥ 0)
  8. tension delta + threshold detection
"""

from copy import deepcopy

from src.engine.effects import calculate_base_effects
from src.engine.interactions import apply_interactions
from src.engine.pacts import apply_pact_modifiers, apply_trade_flows
from src.engine.tension import check_thresholds
from src.engine.types import (
    ActionEffects,
    ActionInput,
    ActionType,
    GameState,
    ResolvedAction,
    TurnResult,
)


def resolve_turn(actions: list[ActionInput], state: GameState) -> TurnResult:
    log: list[str] = []

    base_effects: list[ActionEffects] = [calculate_base_effects(a, state) for a in actions]
    final_effects: list[ActionEffects] = [deepcopy(e) for e in base_effects]

    log.extend(apply_interactions(actions, final_effects, state))
    log.extend(apply_pact_modifiers(actions, final_effects, state))

    for i, action in enumerate(actions):
        _apply_coherence(final_effects[i], action)
        _apply_credibility(final_effects[i], action, state, log)

    trade_flows, trade_log = apply_trade_flows(state)
    log.extend(trade_log)

    final_resources = _consolidate(state, final_effects, trade_flows)

    tension_delta = sum(e.tension_delta for e in final_effects)
    new_tension = max(0, min(100, state.tension + tension_delta))

    threshold_events = check_thresholds(state.tension, new_tension)

    resolved = [
        ResolvedAction(action=a, base_effects=base_effects[i], final_effects=final_effects[i])
        for i, a in enumerate(actions)
    ]

    return TurnResult(
        resolved_actions=resolved,
        final_tension=new_tension,
        threshold_events=threshold_events,
        final_player_resources=final_resources,
        log=log,
    )


def _apply_coherence(effects: ActionEffects, action: ActionInput) -> None:
    """Multiply non-actor resource changes and tension delta by the action's coherence
    multiplier. Actor self-costs (e.g., pact_break DIP penalty) are left untouched —
    you still pay for the attempt even if it lands at 30% effect.
    """
    mult = action.coherence_multiplier
    if mult == 1.0:
        return
    for role_id, changes in effects.resource_changes.items():
        if role_id == action.player_id:
            continue
        for domain in list(changes.keys()):
            changes[domain] = int(changes[domain] * mult)
    effects.tension_delta = int(effects.tension_delta * mult)


def _apply_credibility(
    effects: ActionEffects, action: ActionInput, state: GameState, log: list[str]
) -> None:
    """Diplomatic actions land according to the actor's track record: a faction
    whose word has been kept negotiates at up to 130% effect; a known traitor
    at 70%. Non-diplomatic actions are unaffected — armies don't care about
    your reputation.
    """
    if action.action_type not in (
        ActionType.DIPLOMATIC_PROPOSAL,
        ActionType.DIPLOMATIC_MEDIATION,
    ):
        return
    try:
        credibility = state.get_player(action.player_id).credibility
    except KeyError:
        return
    factor = 0.7 + 0.6 * (credibility / 100.0)
    if abs(factor - 1.0) < 1e-9:
        return
    for role_id, changes in effects.resource_changes.items():
        if role_id == action.player_id:
            continue
        for domain in list(changes.keys()):
            changes[domain] = int(changes[domain] * factor)
    effects.tension_delta = int(effects.tension_delta * factor)
    log.append(
        f"{action.player_id} diplomacy scaled by credibility {credibility} (x{factor:.2f})"
    )


def _consolidate(
    state: GameState,
    effects: list[ActionEffects],
    trade_flows: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    pools: dict[str, dict[str, int]] = {p.id: dict(p.resources) for p in state.players}

    for e in effects:
        for role_id, changes in e.resource_changes.items():
            if role_id not in pools:
                # Unknown target — silently ignore. In a real game this would be a bug,
                # but at the pure-function layer we don't raise.
                continue
            for domain, delta in changes.items():
                pools[role_id][domain] = max(0, pools[role_id].get(domain, 0) + delta)

    for role_id, changes in trade_flows.items():
        if role_id not in pools:
            continue
        for domain, delta in changes.items():
            pools[role_id][domain] = max(0, pools[role_id].get(domain, 0) + delta)

    return pools
