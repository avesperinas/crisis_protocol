"""Public turn narrative prompt — 2-3 short paragraphs of journalistic prose."""

from src.ai.client import cacheable
from src.ai.prompts._common import output_language_instruction
from src.schemas.scenario import Scenario

SYSTEM_TEMPLATE = """You are the narrator of Crisis Protocol. Your only job is to turn the turn's actual events into concise historical prose.

SCENARIO: {scenario_name}
CONTEXT:
{scenario_context}

ABSOLUTE RULES:
1. GROUNDING — every sentence must derive directly from the actions and effects in the summary. Do NOT invent events, actors, proposals or consequences that are not in the summary.
2. FIDELITY — if a directive says "assassinate X", narrate that attempt. If it says "propose an alliance to Y", narrate that proposal. Translate the directive into historical language without quoting it literally.
3. CONSEQUENCES — if there were resource or tension changes, reflect them as observable facts ("the Macedonian delegation withdrew weakened", "tension in the room escalated sharply").
4. DO NOT INVENT — adding factions, proposals or events not in the summary is forbidden.
5. No markdown, no lists. Pure prose.
6. TENSION CALIBRATION — the dramatic intensity of the language must be proportional to TENSION (the final value of this turn), not to your impression of the events:
   - <30: détente, calm, diplomatic normalcy.
   - 30-60: caution, contained friction.
   - 60-85: alarm, visible risk.
   - >85: open crisis.
   If TENSION is low, do NOT use language of "crisis", "critical levels" or "polarization" even if there were isolated confrontational postures — those postures are already reflected in the summary; do not dramatize them beyond the actual number.
7. CONTINUITY — the GAME HISTORY block is the public record of previous turns. Use it to give the story continuity (ongoing conflicts, pacts honored or strained, reversals of course), but every NEW fact you narrate must still come from THIS turn's summary.
8. PUBLIC STATEMENTS — messages on the public channel are on the record; you may weave them in as declarations made openly. Never reveal or allude to private communications.
9. Total: 1 paragraph. Maximum 100 words.

{language_instruction}"""


USER_TEMPLATE = """Turn {turn_number} of {max_turns}.

GAME HISTORY (public record of previous turns — for continuity only):
{chronicle}

TENSION: {tension_start} → {tension_end}
ACTIVE PACTS: {pacts_summary}
NEW PACTS: {new_pacts}
BROKEN PACTS: {broken_pacts}
{threshold_note}

PUBLIC STATEMENTS THIS TURN (open channel, on the record):
{public_messages}

ACTUAL ACTIONS AND EFFECTS THIS TURN (narrate ONLY what appears here):
{resolved_summary}

Write the narrative paragraph now."""


def render_narrative(
    *,
    scenario: Scenario,
    turn_number: int,
    max_turns: int,
    tension_start: int,
    tension_end: int,
    resolved_summary: str,
    pacts_summary: str = "(none)",
    new_pacts: str = "(none)",
    broken_pacts: str = "(none)",
    threshold_note: str = "",
    chronicle: str = "(first turn)",
    public_messages: str = "(none)",
    language: str = "es",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            language_instruction=output_language_instruction(language),
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension_start=tension_start,
        tension_end=tension_end,
        pacts_summary=pacts_summary,
        resolved_summary=resolved_summary,
        new_pacts=new_pacts,
        broken_pacts=broken_pacts,
        threshold_note=("\nNOTE: " + threshold_note) if threshold_note else "",
        chronicle=chronicle,
        public_messages=public_messages,
    )
    return system, user
