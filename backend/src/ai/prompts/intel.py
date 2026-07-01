"""Private intel report prompt — one per player per turn.

The accuracy of the report scales with the player's current INT pool:
- INT >= 12: detailed and accurate
- INT 6..11: 1 accurate fact + 1-2 rumors
- INT < 6: vague, mostly speculation
"""

from src.ai.client import cacheable
from src.ai.prompts._common import output_language_instruction
from src.schemas.scenario import Scenario

SYSTEM_TEMPLATE = """You are the private intelligence service of a faction in Crisis Protocol. You produce ultra-brief internal cables.

SCENARIO: {scenario_name}
CONTEXT:
{scenario_context}

RULES:
- First person, tone of an internal diplomatic cable.
- No markdown, no bullets — prose.
- Total: 3-4 sentences. Maximum 60 words.

CALIBRATION BY INT:
- INT >= 12: 1-2 concrete, reliable facts about other players.
- INT 6..11: 1 concrete fact + 1 unconfirmed rumor.
- INT < 6: all speculative, no concrete names.

{language_instruction}"""


USER_TEMPLATE = """Generate the report for this faction after turn {turn_number}.

PLAYER: {role_name} (current INT: {int_level})

PUBLIC STATE OF THE JUST-RESOLVED TURN:
{public_summary}

WHAT YOU DID:
{own_action}

PRIVATE INFORMATION AVAILABLE TO YOU (use it according to your INT level):
{private_observations}

Write the cable now."""


def render_intel(
    *,
    scenario: Scenario,
    turn_number: int,
    role_name: str,
    int_level: int,
    public_summary: str,
    own_action: str,
    private_observations: str = "(no new private data)",
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
        role_name=role_name,
        int_level=int_level,
        public_summary=public_summary,
        own_action=own_action,
        private_observations=private_observations,
    )
    return system, user
