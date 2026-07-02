"""Deterministic intel engine (Phase D of v2): who learns what after a turn.

Pure function over the resolved turn + game state. It selects the VERIFIED
facts each player is entitled to — Claude then writes the cable prose around
them, but never invents the facts themselves.

Sources of intelligence, in order of strength:
1. Targeted espionage (intel_espionage with INT tokens, not countered):
   the target's literal directive, posture and token allocation; with a
   solid INT pool (>= 8) also ONE secret — an active secret pact the target
   is party to, or failing that a hint of their hidden objective.
2. Counter-intelligence: if someone's espionage against you was exposed,
   you learn who sent it.
3. intel_share pacts: partners share their own operational picture
   (posture, main effort, target).
4. Passive signals, gated by INT pool: about the most "notable" other
   faction this turn (largest tension footprint). INT >= 12 → their literal
   directive; INT 6..11 → posture and main effort only; INT < 6 → nothing.
"""

from src.engine.types import ActionInput, ActionType, GameState, ResolvedAction

_DIRECTIVE_MAX = 160
_OBJECTIVE_MAX = 140

# INT pool needed for espionage to also uncover one secret of the target.
SECRET_THRESHOLD = 8
# INT pool tiers for passive signals.
PASSIVE_FULL = 12
PASSIVE_FUZZY = 6


def compute_private_observations(
    *,
    viewer_id: str,
    resolved_actions: list[ResolvedAction],
    state: GameState,
    int_level: int,
    hidden_objectives: dict[str, str] | None = None,
) -> str | None:
    """The verified facts `viewer_id` learns from this turn, formatted for the
    intel prompt. Returns None when there is nothing to report.
    """
    hidden_objectives = hidden_objectives or {}
    by_actor = {ra.action.player_id: ra for ra in resolved_actions}
    lines: list[str] = []
    espionage_target: str | None = None

    # 1. Targeted espionage.
    viewer_ra = by_actor.get(viewer_id)
    if (
        viewer_ra is not None
        and viewer_ra.action.action_type == ActionType.INTEL_ESPIONAGE
        and viewer_ra.action.target_id
        and viewer_ra.action.tokens.INT >= 1
    ):
        target = viewer_ra.action.target_id
        if viewer_ra.final_effects.espionage_revealed:
            lines.append(
                f"ESPIONAGE FAILED: your operation against {target} was exposed by "
                "counter-intelligence. Your agent was burned and you learned nothing."
            )
        else:
            target_ra = by_actor.get(target)
            if target_ra is not None:
                espionage_target = target
                a = target_ra.action
                lines.append(
                    f"ESPIONAGE SUCCESS on {target}: posture {a.posture}; "
                    f"effort MIL {a.tokens.MIL} / DIP {a.tokens.DIP} / "
                    f"ECO {a.tokens.ECO} / INT {a.tokens.INT}; "
                    f'their directive was: "{_truncate(a.directive, _DIRECTIVE_MAX)}"'
                )
                if int_level >= SECRET_THRESHOLD:
                    secret_line = _one_secret_of(target, state, hidden_objectives)
                    if secret_line:
                        lines.append(secret_line)

    # 2. Counter-intelligence: spies caught targeting the viewer.
    for ra in resolved_actions:
        if (
            ra.action.action_type == ActionType.INTEL_ESPIONAGE
            and ra.action.target_id == viewer_id
            and ra.final_effects.espionage_revealed
        ):
            lines.append(
                f"COUNTER-INTELLIGENCE: you exposed an espionage attempt by "
                f"{ra.action.player_id} against you this turn."
            )

    # 3. intel_share partners volunteer their own picture.
    for pact in state.active_pacts_for(viewer_id):
        if pact.type != "intel_share":
            continue
        partner = pact.player_b_id if pact.player_a_id == viewer_id else pact.player_a_id
        partner_ra = by_actor.get(partner)
        if partner_ra is None:
            continue
        a = partner_ra.action
        target_note = f", directed at {a.target_id}" if a.target_id else ""
        lines.append(
            f"SHARED BY {partner} (intel-share pact): they acted {a.posture}, "
            f"main effort on {_dominant_domain(a)}{target_note}."
        )

    # 4. Passive signals about the most notable other faction.
    if int_level >= PASSIVE_FUZZY:
        notable = _most_notable_other(viewer_id, espionage_target, resolved_actions)
        if notable is not None:
            a = notable.action
            if int_level >= PASSIVE_FULL:
                lines.append(
                    f"NETWORK REPORT on {a.player_id}: posture {a.posture}; "
                    f'their directive was: "{_truncate(a.directive, _DIRECTIVE_MAX)}"'
                )
            else:
                lines.append(
                    f"NETWORK REPORT (partial) on {a.player_id}: posture {a.posture}, "
                    f"main effort on {_dominant_domain(a)}. Details unconfirmed."
                )

    return "\n".join(lines) if lines else None


# ---------- helpers ----------


def _one_secret_of(
    target: str, state: GameState, hidden_objectives: dict[str, str]
) -> str | None:
    """One secret about the target, deterministically chosen: an active secret
    pact first (sorted by pact id for stability), else a hidden-objective hint.
    """
    secret_pacts = sorted(
        (
            p
            for p in state.pacts
            if p.is_active and p.is_secret and target in (p.player_a_id, p.player_b_id)
        ),
        key=lambda p: p.id,
    )
    if secret_pacts:
        p = secret_pacts[0]
        other = p.player_b_id if p.player_a_id == target else p.player_a_id
        return (
            f"SECRET UNCOVERED: {target} maintains a covert {p.type} pact with {other}."
        )
    objective = hidden_objectives.get(target)
    if objective:
        return (
            f"SECRET UNCOVERED: {target}'s hidden agenda appears to be: "
            f'"{_truncate(objective, _OBJECTIVE_MAX)}"'
        )
    return None


def _most_notable_other(
    viewer_id: str, espionage_target: str | None, resolved_actions: list[ResolvedAction]
) -> ResolvedAction | None:
    """The other faction with the largest tension footprint this turn (ties
    broken by role id). Skips the faction already covered by espionage.
    """
    candidates = [
        ra
        for ra in resolved_actions
        if ra.action.player_id not in (viewer_id, espionage_target)
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda ra: (abs(ra.final_effects.tension_delta), ra.action.player_id),
    )


def _dominant_domain(action: ActionInput) -> str:
    t = action.tokens
    pairs = [("MIL", t.MIL), ("DIP", t.DIP), ("ECO", t.ECO), ("INT", t.INT)]
    return max(pairs, key=lambda kv: kv[1])[0]


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
