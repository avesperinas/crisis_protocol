"""Evaluation prompt: parses + scores all actions of a single turn in one call.

Output is a strict JSON object. The parser in ai/parsing.py validates and falls
back to deterministic defaults on failure.

For each action submitted this turn, Claude must produce:
- action_type: one of the engine's ActionType values (or "generic" if unclear)
- target_id: the role_id of the target, or null
- coherence_score: 0.0..1.0 (how well do tokens back the directive?)
- decision_quality: 0..10 (against the role's rubric)
- decision_quality_reasoning: short string

The output is JSON consumed by the engine; `decision_quality_reasoning` is
internal and never shown to players, so this prompt is not localized.
"""

from src.ai.client import cacheable
from src.schemas.scenario import Scenario

# Action types must match src.engine.types.ActionType values.
_ALLOWED_ACTION_TYPES = [
    "military_offensive",
    "military_defensive",
    "diplomatic_proposal",
    "diplomatic_mediation",
    "economic_sanction",
    "economic_aid",
    "intel_espionage",
    "intel_counter",
    "info_expose",
    "pact_break",
    "generic",
]


SYSTEM_TEMPLATE = """You are the evaluation system of Crisis Protocol. You analyze a turn's actions and produce the scores and classifications the engine uses to compute the real effects on resources.

SCENARIO: {scenario_name}
CONTEXT:
{scenario_context}

QUALITY RUBRICS BY FACTION:
{rubrics_block}

AVAILABLE ACTION TYPES (always pick the most specific one possible):
{action_types}

CLASSIFICATION RULES (critical — the engine applies different effects per type):
- "military_offensive": a directive seeking to damage the target's MIL resources. Requires target_id.
- "military_defensive": a directive seeking to protect one's own MIL resources.
- "diplomatic_proposal": a formal offer to another actor. Requires target_id.
- "diplomatic_mediation": intervention to reduce tension between third parties. Requires target_id.
- "economic_sanction": economic pressure against another actor. Requires target_id.
- "economic_aid": transfer of ECO resources to another actor. Requires target_id.
- "intel_espionage": gathering information about another actor. Requires target_id.
- "intel_counter": one's own defense against enemy intelligence operations.
- "info_expose": public disclosure of damaging information about another actor. Requires target_id.
- "pact_break": unilateral breaking of an existing pact. Requires target_id.
- "generic": ONLY if the directive is genuinely vague and fits none of the types above.

KEY RULE: if the directive names a specific actor (its role_id) as the object of the action, you MUST classify it into a non-generic type and put that actor in target_id. Using "generic" with an obvious target is an error.

SCORING RULES:
1. coherence_score 0.0..1.0 — do the invested tokens back the directive?
   - 1.0: tokens perfectly aligned (e.g. high DIP for a diplomatic proposal)
   - 0.7: partially aligned
   - 0.4: insufficient or poorly distributed tokens for the stated ambition
   - 0.0: impossible with those resources

2. decision_quality 0..10 against the role's rubric. Do not reward "winning"; reward "deciding well given what it knew".

NEGOTIATION CONTEXT (game history, active pacts, this turn's messages):
- A directive that follows through on what its faction negotiated this turn (messages) or previously committed to (pacts, prior turns) shows HIGH coherence — the tokens and the diplomacy point the same way.
- A directive that contradicts an explicit promise made in messages, or violates an active pact, is a betrayal. Classify it accurately (e.g. military_offensive), do NOT lower coherence for treachery alone: a well-resourced, deliberate betrayal that serves the faction's hidden objective can score high decision_quality. Penalize decision_quality only when the contradiction looks like blind inconsistency rather than strategy.
- Messages are cheap talk until backed by tokens: never raise coherence for words alone.

3. effective_multiplier 0.3..1.2 — the final multiplier the engine applies to the effects:
   - 1.2: perfect coherence + aligned posture + excellent decision
   - 1.0: baseline, no bonus or penalty
   - 0.5: low coherence or contradictory posture
   - 0.3: incoherent directive or obvious bluff

4. promise_assessment — did this action honor or contradict the faction's EXPLICIT commitments?
   - "kept": the action follows through on a concrete promise the faction made (in this turn's messages or in an active pact) when it had a real chance to defect. Routine behavior with no commitment at stake is NOT "kept".
   - "broken": the action directly contradicts an explicit promise the faction made in messages, or violates an active pact (e.g. attacking a non-aggression partner).
   - "none": no explicit commitment was at stake this turn. This is the common case — be conservative; vague friendly talk is not a promise.
   "promise_note" is one short sentence naming the commitment (empty when "none"). The note may be quoted in the public narrative, so write it as an observable fact and never reveal secret pacts in it.

IMPORTANT — BREVITY: "decision_quality_reasoning" is internal (not shown to the user). At most one short sentence per action. You evaluate several factions in the same response — do not go long on any of them, or you will run out of space for the last ones.

RETURN JSON ONLY. No text outside the JSON. No markdown or code fences:

{{
  "evaluations": [
    {{
      "player_id": "...",
      "action_type": "diplomatic_proposal",
      "target_id": "atenas",
      "coherence_score": 0.85,
      "posture_modifier": 0.10,
      "decision_quality": 7.0,
      "decision_quality_reasoning": "...",
      "effective_multiplier": 1.05,
      "promise_assessment": "none",
      "promise_note": ""
    }}
  ]
}}"""


USER_TEMPLATE = """Turn {turn_number} of {max_turns}. Global tension at start: {tension_start}.

ACTIVE PACTS:
{pacts_block}

GAME HISTORY (public record of previous turns):
{previous_events}

MESSAGES SENT THIS TURN (as referee you see all channels; players only see what involves them):
{messages_block}

ACTIONS THIS TURN (player_id is each faction's role_id):

{actions_block}

Return the JSON now."""


def render_evaluation(
    *,
    scenario: Scenario,
    turn_number: int,
    max_turns: int,
    tension_start: int,
    actions: list[dict],
    active_pacts: list[dict] | None = None,
    previous_events: str = "(none)",
    messages_block: str = "(none)",
) -> tuple[list[dict], str]:
    """Return (system_blocks, user_message).

    `actions` is a list of dicts shaped:
        {"player_id": "macedonia", "posture": "confrontational",
         "tokens": {"MIL": 2, "DIP": 1, "ECO": 0, "INT": 1},
         "directive": "..."}

    `active_pacts` shape: [{"a": "...", "b": "...", "type": "alliance", "is_secret": false}]
    `previous_events` is the game chronicle (public record of past turns).
    `messages_block` lists this turn's messages, public and private.
    """
    rubrics = "\n\n".join(
        f"- {f.id} ({f.name}): {f.evaluation_rubric}" for f in scenario.factions
    )
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            rubrics_block=rubrics,
            action_types=", ".join(_ALLOWED_ACTION_TYPES),
        )
    )

    if active_pacts:
        pacts_block = "\n".join(
            f"- {p['a']} <-> {p['b']}: {p['type']}" + (" (secret)" if p.get("is_secret") else "")
            for p in active_pacts
        )
    else:
        pacts_block = "(none)"

    actions_block = "\n\n".join(
        f"{i + 1}. player_id: {a['player_id']}\n"
        f"   posture: {a['posture']}\n"
        f"   tokens: MIL={a['tokens']['MIL']} DIP={a['tokens']['DIP']} "
        f"ECO={a['tokens']['ECO']} INT={a['tokens']['INT']}\n"
        f"   directive: {a['directive']!r}"
        for i, a in enumerate(actions)
    )

    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension_start=tension_start,
        pacts_block=pacts_block,
        previous_events=previous_events,
        messages_block=messages_block,
        actions_block=actions_block,
    )
    return system, user
