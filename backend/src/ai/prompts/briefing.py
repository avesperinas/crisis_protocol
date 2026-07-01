"""Briefing prompt: per-player private intro at game start.

Stable part (scenario context) goes in `system` as a cacheable block;
the variable part (this player's role + resources + objectives) is the
user message.
"""

from src.ai.client import cacheable
from src.ai.prompts._common import output_language_instruction
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """You are a game designer writing the private briefing for a player in a game of Crisis Protocol.

SCENARIO: {scenario_name} ({scenario_year})
TYPE: {scenario_type}

HISTORICAL CONTEXT:
{scenario_context}

TONE RULES:
- Serious, evocative, no epic clichés.
- Narrative prose, no bullet lists inside the text.
- Address the player in the second person.
- Do not reveal the hidden objectives of other factions.
- Do not mention mechanics (tokens, multipliers, etc.).

REQUIRED STRUCTURE — four markdown H2 sections, in this exact order, with the
heading text written in the output language:
1. The Situation
2. Your Position
3. What You Know
4. What You Must Achieve

Total maximum: 250 words.

{language_instruction}"""


USER_TEMPLATE = """Generate the player's briefing from this information:

ROLE: {faction_name} — {faction_tagline}
ROLE DESCRIPTION:
{faction_description}

STARTING RESOURCES:
- Military (MIL): {mil}
- Diplomatic (DIP): {dip}
- Economic (ECO): {eco}
- Intelligence (INT): {int_}

PUBLIC OBJECTIVE (visible to everyone):
{public_objective}

HIDDEN OBJECTIVE (for this player only — narrate it without stating it literally):
{hidden_objective}

STRATEGIC CONSIDERATIONS FOR THE ROLE (internal rubric; informs tone, do not quote verbatim):
{rubric}

Write the briefing now."""


def render_briefing(
    scenario: Scenario, faction: Faction, language: str = "es"
) -> tuple[list[dict], str]:
    """Returns (system_blocks, user_message) ready for ClaudeClient.call()."""
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_year=scenario.year,
            scenario_type=scenario.type,
            scenario_context=scenario.context,
            language_instruction=output_language_instruction(language),
        )
    )
    user = USER_TEMPLATE.format(
        faction_name=faction.name,
        faction_tagline=faction.tagline,
        faction_description=faction.description,
        mil=faction.starting_resources.MIL,
        dip=faction.starting_resources.DIP,
        eco=faction.starting_resources.ECO,
        int_=faction.starting_resources.INT,
        public_objective=faction.public_objective.text,
        hidden_objective=faction.hidden_objective.text,
        rubric=faction.evaluation_rubric,
    )
    return system, user
