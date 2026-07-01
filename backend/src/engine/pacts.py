"""Per-action pact modifiers and per-turn trade flows.

Per-action: alliance bonus (+15%) and non-aggression penalty (-30%).
Per-turn: trade pact resource exchange between members.
"""

from src.engine.types import ActionEffects, ActionInput, ActionType, GameState


def apply_pact_modifiers(
    actions: list[ActionInput],
    effects: list[ActionEffects],
    state: GameState,
) -> list[str]:
    log: list[str] = []
    by_actor = {a.player_id: a for a in actions}

    for i, action in enumerate(actions):
        if action.target_id is None:
            continue
        for pact in state.pacts:
            if not pact.is_active:
                continue
            partner = _partner(pact, action.player_id)
            if partner is None:
                continue

            if pact.type == "alliance":
                ally_action = by_actor.get(partner)
                if ally_action and ally_action.target_id == action.target_id:
                    _scale_target_changes(effects[i], action.target_id, 1.15)
                    log.append(
                        f"{action.player_id} alliance with {partner}: +15% on action vs "
                        f"{action.target_id}"
                    )

            if (
                pact.type == "non_aggression"
                and action.target_id == partner
                and action.action_type == ActionType.MILITARY_OFFENSIVE
            ):
                _scale_target_changes(effects[i], action.target_id, 0.70)
                log.append(
                    f"{action.player_id} non-aggression with {partner}: -30% on offensive"
                )

    return log


def apply_trade_flows(state: GameState) -> tuple[dict[str, dict[str, int]], list[str]]:
    """Compute per-turn resource transfers from active trade pacts.

    Returns role_id -> domain -> delta, plus a log of what flowed.
    """
    flows: dict[str, dict[str, int]] = {}
    log: list[str] = []
    for pact in state.pacts:
        if not pact.is_active or pact.type != "trade":
            continue
        terms = pact.terms or {}
        a_gives: dict[str, int] = terms.get("a_gives", {"ECO": 1})
        b_gives: dict[str, int] = terms.get("b_gives", {"DIP": 1})
        for domain, amount in a_gives.items():
            _flow(flows, pact.player_a_id, domain, -amount)
            _flow(flows, pact.player_b_id, domain, amount)
        for domain, amount in b_gives.items():
            _flow(flows, pact.player_b_id, domain, -amount)
            _flow(flows, pact.player_a_id, domain, amount)
        log.append(
            f"Trade pact {pact.player_a_id}<->{pact.player_b_id}: "
            f"a_gives={a_gives}, b_gives={b_gives}"
        )
    return flows, log


def _partner(pact, role_id: str) -> str | None:
    if pact.player_a_id == role_id:
        return pact.player_b_id
    if pact.player_b_id == role_id:
        return pact.player_a_id
    return None


def _scale_target_changes(effects: ActionEffects, target_id: str, factor: float) -> None:
    target_changes = effects.resource_changes.get(target_id)
    if not target_changes:
        return
    for domain in list(target_changes.keys()):
        target_changes[domain] = int(target_changes[domain] * factor)


def _flow(flows: dict[str, dict[str, int]], role_id: str, domain: str, delta: int) -> None:
    flows.setdefault(role_id, {})
    flows[role_id][domain] = flows[role_id].get(domain, 0) + delta
