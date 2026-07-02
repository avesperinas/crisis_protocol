"""Bot decision prompt.

System block is stable per (scenario, role) for the whole game — caches well
across turns. The user block holds the current state.
"""

from src.ai.client import cacheable
from src.ai.prompts._common import language_name
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """You are an intelligent Crisis Protocol player taking on the role of {role_name} ({role_tagline}) in the scenario "{scenario_name}".

SCENARIO CONTEXT:
{scenario_context}

YOUR PRIVATE BRIEFING:
{briefing}

DECISION-QUALITY RUBRIC FOR YOUR ROLE (use it to guide your reasoning, do not quote it verbatim):
{rubric}

ACTION TYPES THAT EXIST (you do not return them, but think with them when writing your directive):
- military_offensive, military_defensive
- diplomatic_proposal, diplomatic_mediation
- economic_sanction, economic_aid
- intel_espionage, intel_counter
- info_expose
- pact_break
- generic (if you only want to hold position)

RULES:
- Make decisions consistent with your role, your resources, your public position.
- Be strategic but NOT optimal — you are a human actor with biases and doubts. Allow a degree of imperfection.
- Consider betrayals, tactical alliances and bluffs when they serve your hidden objective.
- REACT to diplomacy: if another faction messaged you or addressed you publicly this turn, factor it into your decision — honor it, exploit it or distrust it, in character. Remember what happened in previous turns (the game history): grudges, kept promises and past betrayals should shape how you treat each faction.
- The "directive" is free text written in {language_name}: describe your concrete intention (with whom, toward what end). Max 250 characters.
- If the directive names another actor, use its name or role_id (e.g. macedonia, atenas, esparta, tebas, corinto, persia).

RETURN JSON ONLY with this exact shape (no text outside, no code fences):

{{
  "posture": "confrontational" | "cooperative" | "ambiguous",
  "tokens": {{"MIL": 0, "DIP": 0, "ECO": 0, "INT": 0}},
  "directive": "...",
  "reasoning": "..."
}}

HARD CONSTRAINTS:
- The tokens must sum to EXACTLY {token_budget}. No negative tokens.
- "posture" is exactly one of the three values.
- "directive" MUST be written in {language_name}.
- "reasoning" is internal (not shown to the user): at most 2 short sentences. Do not go long."""


USER_TEMPLATE = """CURRENT STATE — turn {turn_number} of {max_turns}.

Global tension: {tension}/100.
Your persistent resources:
- MIL: {mil}
- DIP: {dip}
- ECO: {eco}
- INT: {int_}
Budget this turn: {token_budget} tokens.

Active pacts in the game:
{pacts_block}

GAME HISTORY (public record of previous turns):
{chronicle}

MESSAGES THIS TURN VISIBLE TO YOU (public channel + private ones involving you):
{messages_block}

Your intelligence report from the previous turn:
{previous_intel}

Decide your action now. JSON only."""


def render_bot_decision(
    *,
    scenario: Scenario,
    faction: Faction,
    briefing: str,
    turn_number: int,
    max_turns: int,
    tension: int,
    resources: dict[str, int],
    token_budget: int,
    pacts_summary: str = "(none)",
    chronicle: str = "(first turn — no history yet)",
    messages_block: str = "(none)",
    previous_intel: str = "(no previous report)",
    language: str = "es",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            role_name=faction.name,
            role_tagline=faction.tagline,
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            briefing=briefing,
            rubric=faction.evaluation_rubric,
            token_budget=token_budget,
            language_name=language_name(language),
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension=tension,
        mil=resources.get("MIL", 0),
        dip=resources.get("DIP", 0),
        eco=resources.get("ECO", 0),
        int_=resources.get("INT", 0),
        token_budget=token_budget,
        pacts_block=pacts_summary,
        chronicle=chronicle,
        messages_block=messages_block,
        previous_intel=previous_intel,
    )
    return system, user
