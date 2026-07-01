"""Pairwise interaction rules applied after base effects.

Operates on a parallel list of ActionEffects aligned 1:1 with the actions list.
Mutates in place to keep logic simple; the resolver hands us copies.
"""

from src.engine.types import ActionEffects, ActionInput, ActionType, GameState


def apply_interactions(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    state: GameState,
) -> list[str]:
    log: list[str] = []
    by_actor = {a.player_id: i for i, a in enumerate(actions)}

    _resolve_attack_vs_defense(actions, effects, by_actor, log)
    _resolve_espionage_vs_counter(actions, effects, by_actor, log)
    _resolve_sanction_vs_trade_pact(actions, effects, state, log)
    _resolve_mediation(actions, effects, log)

    return log


def _resolve_attack_vs_defense(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    by_actor: dict[str, int],
    log: list[str],
) -> None:
    """If target defended with MIL ≥ 50% of attacker's MIL, damage reduced to 40%."""
    for i, action in enumerate(actions):
        if action.action_type != ActionType.MILITARY_OFFENSIVE or action.target_id is None:
            continue
        target_idx = by_actor.get(action.target_id)
        if target_idx is None:
            continue
        target_action = actions[target_idx]
        if target_action.action_type != ActionType.MILITARY_DEFENSIVE:
            continue
        attacker_mil = action.tokens.MIL
        defender_mil = target_action.tokens.MIL
        if defender_mil * 2 >= attacker_mil:  # equivalent to defender >= attacker * 0.5
            target_changes = effects[i].resource_changes.get(action.target_id, {})
            if "MIL" in target_changes:
                original = target_changes["MIL"]
                target_changes["MIL"] = int(original * 0.4)
                log.append(
                    f"{action.player_id} attack on {action.target_id} reduced by defense: "
                    f"{original} -> {target_changes['MIL']}"
                )


def _resolve_espionage_vs_counter(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    by_actor: dict[str, int],
    log: list[str],
) -> None:
    """If counter-intel INT ≥ espionage INT, spy fails and is revealed (loses tokens.INT in pool)."""
    for i, action in enumerate(actions):
        if action.action_type != ActionType.INTEL_ESPIONAGE or action.target_id is None:
            continue
        target_idx = by_actor.get(action.target_id)
        if target_idx is None:
            continue
        target_action = actions[target_idx]
        if target_action.action_type != ActionType.INTEL_COUNTER:
            continue
        if target_action.tokens.INT >= action.tokens.INT:
            effects[i].espionage_revealed = True
            effects[i].add_resource_change(action.player_id, "INT", -action.tokens.INT)
            log.append(
                f"{action.player_id} espionage on {action.target_id} failed; spy revealed"
            )


def _resolve_sanction_vs_trade_pact(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    state: GameState,
    log: list[str],
) -> None:
    """Target with an active trade pact takes 25% less ECO damage from a sanction."""
    for i, action in enumerate(actions):
        if action.action_type != ActionType.ECONOMIC_SANCTION or action.target_id is None:
            continue
        protected = any(
            p.is_active
            and p.type == "trade"
            and action.target_id in (p.player_a_id, p.player_b_id)
            for p in state.pacts
        )
        if not protected:
            continue
        target_changes = effects[i].resource_changes.get(action.target_id, {})
        if "ECO" in target_changes:
            original = target_changes["ECO"]
            target_changes["ECO"] = int(original * 0.75)
            log.append(
                f"{action.player_id} sanction on {action.target_id} reduced 25% by trade pact"
            )


def _resolve_mediation(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    log: list[str],
) -> None:
    """Mediation fails if the targeted party or anyone targeting them performs an offensive
    military action in the same turn. Failure: cancel the -8 tension, replace with +5,
    and revoke the mediator's DIP reward.
    """
    for i, action in enumerate(actions):
        if action.action_type != ActionType.DIPLOMATIC_MEDIATION or action.target_id is None:
            continue
        target = action.target_id
        any_attack_involving_target = any(
            o.action_type == ActionType.MILITARY_OFFENSIVE
            and target in (o.player_id, o.target_id)
            for o in actions
        )
        if any_attack_involving_target:
            # The base effect set tension -= 8; cancel it and set +5 instead.
            effects[i].tension_delta += 13
            actor_changes = effects[i].resource_changes.get(action.player_id, {})
            actor_changes.pop("DIP", None)
            if not actor_changes:
                effects[i].resource_changes.pop(action.player_id, None)
            log.append(
                f"{action.player_id} mediation involving {target} failed; tension increases"
            )
