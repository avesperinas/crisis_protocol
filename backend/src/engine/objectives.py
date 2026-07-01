"""Executable evaluators for scenario objectives.

Each evaluator: (history: GameHistory) -> bool. Registered under (scenario_id, role_id, kind).
Lookup via evaluate_objective(scenario_id, role_id, kind, history).
"""

from collections.abc import Callable
from typing import Literal

from src.engine.types import ActionType, GameHistory

Kind = Literal["public", "hidden"]
Evaluator = Callable[[GameHistory], bool]

_REGISTRY: dict[tuple[str, str, Kind], Evaluator] = {}


def register(scenario_id: str, role_id: str, kind: Kind, fn: Evaluator) -> None:
    _REGISTRY[(scenario_id, role_id, kind)] = fn


def evaluate_objective(scenario_id: str, role_id: str, kind: Kind, history: GameHistory) -> bool:
    key = (scenario_id, role_id, kind)
    if key not in _REGISTRY:
        raise KeyError(f"No objective evaluator registered for {key!r}")
    return _REGISTRY[key](history)


# --------- Corinth (corinth_338) evaluators ---------

_SCENARIO = "corinth_338"


def _initial(history: GameHistory, role: str, domain: str) -> int:
    return history.initial_resources.get(role, {}).get(domain, 0)


def _current(history: GameHistory, role: str, domain: str) -> int:
    return history.state.get_player(role).resources.get(domain, 0)


def _alliance_count_for(history: GameHistory, role: str, exclude: set[str] | None = None) -> int:
    exclude = exclude or set()
    count = 0
    for pact in history.state.pacts:
        if not pact.is_active or pact.type != "alliance":
            continue
        if role not in (pact.player_a_id, pact.player_b_id):
            continue
        other = pact.player_b_id if pact.player_a_id == role else pact.player_a_id
        if other in exclude:
            continue
        count += 1
    return count


def macedonia_public(history: GameHistory) -> bool:
    """≥3 alliance pacts with non-Persia factions."""
    return _alliance_count_for(history, "macedonia", exclude={"persia"}) >= 3


def macedonia_hidden(history: GameHistory) -> bool:
    """Atenas-Macedonia alliance active AND Macedonia never attacked Atenas."""
    if not history.state.has_pact_between("macedonia", "atenas", "alliance"):
        return False
    for turn in history.turns:
        for action in turn.actions:
            if (
                action.player_id == "macedonia"
                and action.target_id == "atenas"
                and action.action_type == ActionType.MILITARY_OFFENSIVE
            ):
                return False
    return True


def atenas_public(history: GameHistory) -> bool:
    """Fleet preserved: Atenas MIL ≥ 80% of initial."""
    initial = _initial(history, "atenas", "MIL")
    if initial == 0:
        return False
    return _current(history, "atenas", "MIL") >= initial * 0.8


def atenas_hidden(history: GameHistory) -> bool:
    """Secret intel_share or trade pact with Persia, never exposed."""
    for pact in history.state.pacts:
        if not pact.is_active or not pact.is_secret:
            continue
        if pact.type not in ("intel_share", "trade"):
            continue
        if {pact.player_a_id, pact.player_b_id} != {"atenas", "persia"}:
            continue
        if pact.id in history.exposed_pacts:
            continue
        return True
    return False


def esparta_public(history: GameHistory) -> bool:
    """No alliance with Macedonia."""
    return not history.state.has_pact_between("esparta", "macedonia", "alliance")


def esparta_hidden(history: GameHistory) -> bool:
    """At least one diplomatic_proposal exchanged between Esparta and Macedonia."""
    for turn in history.turns:
        for action in turn.actions:
            if action.action_type != ActionType.DIPLOMATIC_PROPOSAL:
                continue
            pair = {action.player_id, action.target_id}
            if pair == {"esparta", "macedonia"}:
                return True
    return False


def tebas_public(history: GameHistory) -> bool:
    """At least one active pact AND MIL ≥ 50% of initial (no successful crushing)."""
    has_pact = any(
        p.is_active and "tebas" in (p.player_a_id, p.player_b_id)
        for p in history.state.pacts
    )
    if not has_pact:
        return False
    initial = _initial(history, "tebas", "MIL")
    if initial == 0:
        return True
    return _current(history, "tebas", "MIL") >= initial * 0.5


def tebas_hidden(history: GameHistory) -> bool:
    """Alliance with Macedonia AND Atenas weakened (broken pact, or MIL/ECO drop ≥30%)."""
    if not history.state.has_pact_between("tebas", "macedonia", "alliance"):
        return False
    atenas_broken = any(
        not p.is_active and "atenas" in (p.player_a_id, p.player_b_id)
        for p in history.state.pacts
    )
    if atenas_broken:
        return True
    initial_mil = _initial(history, "atenas", "MIL")
    initial_eco = _initial(history, "atenas", "ECO")
    cur_mil = _current(history, "atenas", "MIL")
    cur_eco = _current(history, "atenas", "ECO")
    mil_drop = (initial_mil - cur_mil) / max(1, initial_mil)
    eco_drop = (initial_eco - cur_eco) / max(1, initial_eco)
    return mil_drop >= 0.30 or eco_drop >= 0.30


def corinto_public(history: GameHistory) -> bool:
    """≥2 active trade pacts AND ECO increased over initial."""
    trade_count = sum(
        1 for p in history.state.pacts
        if p.is_active and p.type == "trade" and "corinto" in (p.player_a_id, p.player_b_id)
    )
    if trade_count < 2:
        return False
    return _current(history, "corinto", "ECO") > _initial(history, "corinto", "ECO")


def corinto_hidden(history: GameHistory) -> bool:
    """Atenas MIL reduced ≥25% from initial."""
    initial = _initial(history, "atenas", "MIL")
    if initial == 0:
        return False
    return (initial - _current(history, "atenas", "MIL")) / initial >= 0.25


def persia_public(history: GameHistory) -> bool:
    """Macedonia has fewer than 3 Greek alliances — i.e., the negation of Macedonia public."""
    return not macedonia_public(history)


def persia_hidden(history: GameHistory) -> bool:
    """At least one broken pact between league members (non-Persia parties), OR a
    secret Atenas-Persia pact still active and unexposed."""
    league_pact_broken = any(
        not p.is_active
        and p.broken_turn is not None
        and "persia" not in (p.player_a_id, p.player_b_id)
        for p in history.state.pacts
    )
    if league_pact_broken:
        return True
    for pact in history.state.pacts:
        if not pact.is_active or not pact.is_secret:
            continue
        if {pact.player_a_id, pact.player_b_id} != {"atenas", "persia"}:
            continue
        if pact.id not in history.exposed_pacts:
            return True
    return False


# Register all Corinth evaluators at import.
for role, public_fn, hidden_fn in [
    ("macedonia", macedonia_public, macedonia_hidden),
    ("atenas", atenas_public, atenas_hidden),
    ("esparta", esparta_public, esparta_hidden),
    ("tebas", tebas_public, tebas_hidden),
    ("corinto", corinto_public, corinto_hidden),
    ("persia", persia_public, persia_hidden),
]:
    register(_SCENARIO, role, "public", public_fn)
    register(_SCENARIO, role, "hidden", hidden_fn)


# --------- Oil Crisis (oil_crisis_1973) evaluators ---------

_OIL = "oil_crisis_1973"


def _max_tension(history: GameHistory) -> int:
    values = [t.tension_at_start for t in history.turns] + [t.tension_at_end for t in history.turns]
    return max(values) if values else history.state.tension


def _active_pact(history: GameHistory, a: str, b: str, types: set[str] | None = None) -> bool:
    for p in history.state.pacts:
        if not p.is_active:
            continue
        if {p.player_a_id, p.player_b_id} != {a, b}:
            continue
        if types and p.type not in types:
            continue
        return True
    return False


def _broken_pact(history: GameHistory, a: str, b: str) -> bool:
    return any(
        not p.is_active and p.broken_turn is not None and {p.player_a_id, p.player_b_id} == {a, b}
        for p in history.state.pacts
    )


def arabia_saudi_public(history: GameHistory) -> bool:
    has_pact = _active_pact(history, "arabia_saudi", "eeuu", {"non_aggression", "alliance"})
    return has_pact and (_max_tension(history) - history.state.tension) >= 10


def arabia_saudi_hidden(history: GameHistory) -> bool:
    initial = _initial(history, "arabia_saudi", "ECO")
    if initial == 0 or not _active_pact(history, "arabia_saudi", "eeuu", {"alliance"}):
        return False
    return _current(history, "arabia_saudi", "ECO") >= initial * 0.8


def oil_eeuu_public(history: GameHistory) -> bool:
    allies = [o for o in ("europa", "japon") if _active_pact(history, "eeuu", o)]
    if len(allies) < 2:
        return False
    return not any(_broken_pact(history, "eeuu", o) for o in ("europa", "japon"))


def oil_eeuu_hidden(history: GameHistory) -> bool:
    start = history.turns[0].tension_at_start if history.turns else history.state.tension
    tension_dropped = (start - history.state.tension) >= 15
    return tension_dropped and not _active_pact(history, "urss", "arabia_saudi", {"alliance"})


def iran_public(history: GameHistory) -> bool:
    return _current(history, "iran", "ECO") - _initial(history, "iran", "ECO") >= 3


def iran_hidden(history: GameHistory) -> bool:
    western_trade = any(_active_pact(history, "iran", w, {"trade"}) for w in ("europa", "japon", "eeuu"))
    return history.state.tension >= 60 and western_trade


def europa_public(history: GameHistory) -> bool:
    return any(_active_pact(history, "europa", p, {"trade"}) for p in ("arabia_saudi", "iran"))


def europa_hidden(history: GameHistory) -> bool:
    has_pact = any(_active_pact(history, "europa", p) for p in ("arabia_saudi", "iran"))
    return has_pact and not _broken_pact(history, "europa", "eeuu")


def japon_public(history: GameHistory) -> bool:
    return any(_active_pact(history, "japon", p, {"trade", "alliance"}) for p in ("arabia_saudi", "iran"))


def japon_hidden(history: GameHistory) -> bool:
    secret_producers = [
        (p.player_a_id if p.player_b_id == "japon" else p.player_b_id)
        for p in history.state.pacts
        if p.is_active and p.is_secret and p.type in ("trade", "intel_share")
        and "japon" in (p.player_a_id, p.player_b_id)
    ]
    candidates = [p for p in secret_producers if p in ("arabia_saudi", "iran")]
    if not candidates:
        return False
    return not _active_pact(history, "eeuu", candidates[0], {"alliance"})


def urss_public(history: GameHistory) -> bool:
    return _active_pact(history, "urss", "arabia_saudi") or _active_pact(history, "urss", "europa")


def urss_hidden(history: GameHistory) -> bool:
    return history.state.tension >= 55 and not _active_pact(history, "eeuu", "arabia_saudi", {"alliance"})


for role, public_fn, hidden_fn in [
    ("arabia_saudi", arabia_saudi_public, arabia_saudi_hidden),
    ("eeuu", oil_eeuu_public, oil_eeuu_hidden),
    ("iran", iran_public, iran_hidden),
    ("europa", europa_public, europa_hidden),
    ("japon", japon_public, japon_hidden),
    ("urss", urss_public, urss_hidden),
]:
    register(_OIL, role, "public", public_fn)
    register(_OIL, role, "hidden", hidden_fn)


# --------- Arctic Crisis (arctic_2031) evaluators ---------

_ARCTIC = "arctic_2031"


def rusia_public(history: GameHistory) -> bool:
    return history.state.has_pact_between("rusia", "china")


def rusia_hidden(history: GameHistory) -> bool:
    # "Early" means before the final turn, not literally turn 1-3 — real
    # negotiations take a turn or two to mature into a signed pact.
    early_pact = any(
        p.is_active and p.type in ("trade", "alliance") and p.created_turn < history.state.max_turns
        and {p.player_a_id, p.player_b_id} == {"rusia", "china"}
        for p in history.state.pacts
    )
    if not early_pact:
        return False
    china_western = history.state.has_pact_between("china", "eeuu") or history.state.has_pact_between(
        "china", "canada"
    )
    return not china_western


def arctic_eeuu_public(history: GameHistory) -> bool:
    has_alliance = history.state.has_pact_between("eeuu", "canada", "alliance")
    return has_alliance and not history.state.has_pact_between("china", "rusia")


def arctic_eeuu_hidden(history: GameHistory) -> bool:
    has_alliance = history.state.has_pact_between("eeuu", "canada", "alliance")
    canada_clean = not history.state.has_pact_between(
        "canada", "china"
    ) and not history.state.has_pact_between("canada", "rusia")
    return has_alliance and canada_clean


def canada_public(history: GameHistory) -> bool:
    has_alliance = history.state.has_pact_between("canada", "eeuu", "alliance")
    broke_non_aggression = any(
        not p.is_active
        and p.type == "non_aggression"
        and "canada" in (p.player_a_id, p.player_b_id)
        and p.broken_by_player_id == "canada"
        for p in history.state.pacts
    )
    return has_alliance and not broke_non_aggression


def canada_hidden(history: GameHistory) -> bool:
    # Same relaxed timing as rusia_hidden — see comment there.
    early_alliance = any(
        p.is_active and p.type == "alliance" and p.created_turn < history.state.max_turns
        and {p.player_a_id, p.player_b_id} == {"canada", "eeuu"}
        for p in history.state.pacts
    )
    if not early_alliance:
        return False
    return _current(history, "canada", "ECO") > _initial(history, "canada", "ECO")


def noruega_public(history: GameHistory) -> bool:
    partners = {
        (p.player_a_id if p.player_b_id == "noruega" else p.player_b_id)
        for p in history.state.pacts
        if p.is_active and "noruega" in (p.player_a_id, p.player_b_id)
    }
    if len(partners) < 3:
        return False
    return bool(partners & {"eeuu", "canada"}) and bool(partners & {"rusia", "china"})


def noruega_hidden(history: GameHistory) -> bool:
    has_china = history.state.has_pact_between("noruega", "china")
    has_western = history.state.has_pact_between("noruega", "eeuu") or history.state.has_pact_between(
        "noruega", "canada"
    )
    return has_china and has_western


def china_public(history: GameHistory) -> bool:
    partners = {
        (p.player_a_id if p.player_b_id == "china" else p.player_b_id)
        for p in history.state.pacts
        if p.is_active and "china" in (p.player_a_id, p.player_b_id)
    }
    return len(partners & {"rusia", "canada", "noruega", "groenlandia"}) >= 2


def china_hidden(history: GameHistory) -> bool:
    attempted_offensive = any(
        action.player_id == "china" and action.action_type == ActionType.MILITARY_OFFENSIVE
        for turn in history.turns
        for action in turn.actions
    )
    if not attempted_offensive:
        return False
    return history.state.has_pact_between("china", "rusia") or history.state.has_pact_between(
        "china", "groenlandia"
    )


def groenlandia_public(history: GameHistory) -> bool:
    return _current(history, "groenlandia", "ECO") - _initial(history, "groenlandia", "ECO") >= 4


def groenlandia_hidden(history: GameHistory) -> bool:
    partners = {
        (p.player_a_id if p.player_b_id == "groenlandia" else p.player_b_id)
        for p in history.state.pacts
        if p.is_active and "groenlandia" in (p.player_a_id, p.player_b_id)
    }
    return bool(partners & {"eeuu", "canada", "noruega"}) and bool(partners & {"rusia", "china"})


for role, public_fn, hidden_fn in [
    ("rusia", rusia_public, rusia_hidden),
    ("eeuu", arctic_eeuu_public, arctic_eeuu_hidden),
    ("canada", canada_public, canada_hidden),
    ("noruega", noruega_public, noruega_hidden),
    ("china", china_public, china_hidden),
    ("groenlandia", groenlandia_public, groenlandia_hidden),
]:
    register(_ARCTIC, role, "public", public_fn)
    register(_ARCTIC, role, "hidden", hidden_fn)
