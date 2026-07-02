"""Bot message reply prompt — an in-character diplomatic reply to a message.

The system block is stable per (scenario, role) and caches well. The user
block carries the game state, the conversation with the sender and the
incoming message. Output is plain text (no JSON): the reply itself.
"""

from src.ai.client import cacheable
from src.ai.prompts._common import language_name
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """You are {role_name} ({role_tagline}) in Crisis Protocol, scenario "{scenario_name}". Another faction has sent you a diplomatic message and you must reply in character.

SCENARIO CONTEXT:
{scenario_context}

YOUR PRIVATE BRIEFING:
{briefing}

RULES:
- Reply as the leader of your delegation: first person, diplomatic register, in character.
- Be strategic: you may commit, evade, probe, bluff or set conditions. Never reveal your hidden objective outright.
- Keep continuity with the game history and your active pacts; do not reference private information the sender cannot know you have.
- Do not invent game mechanics, events or third-party actions that have not happened.
- 1-3 sentences, maximum 60 words. No markdown, no quotes around the reply, no signature.
- Write the reply in {language_name}.

Return ONLY the reply text."""


USER_TEMPLATE = """CURRENT STATE — turn {turn_number} of {max_turns}. Global tension: {tension}/100.

Active pacts you know of:
{pacts_block}

GAME HISTORY (public record of previous turns):
{chronicle}

YOUR CONVERSATION WITH {sender_name} ({sender_id}) THIS GAME (oldest first):
{thread_block}

NEW MESSAGE FROM {sender_name}:
{incoming}

Write your reply now."""


def render_bot_message_reply(
    *,
    scenario: Scenario,
    faction: Faction,
    briefing: str,
    sender_id: str,
    sender_name: str,
    incoming: str,
    turn_number: int,
    max_turns: int,
    tension: int,
    pacts_summary: str = "(none)",
    chronicle: str = "(first turn — no history yet)",
    thread_block: str = "(no previous messages)",
    language: str = "es",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            role_name=faction.name,
            role_tagline=faction.tagline,
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            briefing=briefing,
            language_name=language_name(language),
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension=tension,
        pacts_block=pacts_summary,
        chronicle=chronicle,
        sender_id=sender_id,
        sender_name=sender_name,
        thread_block=thread_block,
        incoming=incoming,
    )
    return system, user
