"""Bot pact response prompt: should this bot accept or reject an incoming pact proposal?"""

from src.ai.client import cacheable
from src.ai.prompts._common import language_name
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """You are {role_name} ({role_tagline}) in Crisis Protocol, scenario "{scenario_name}". You have just received a pact proposal and must decide whether to accept.

SCENARIO CONTEXT:
{scenario_context}

YOUR BRIEFING:
{briefing}

INTERNAL RUBRIC (informs your decision, do not quote it):
{rubric}

PACT TYPES AND EFFECTS:
- alliance: +15% effectiveness on actions against shared targets
- non_aggression: -30% damage on mutual aggression
- trade: resource exchange each turn
- intel_share: more detailed intelligence reports

RULES:
- Accept only if the pact serves your objectives. Note that pacts are recorded publicly.
- If your hidden objective would be compromised or exposed, reject.
- If the proposer is a natural rival and the pact weakens you strategically, reject.
- If the pact strengthens your position at no obvious cost, accept.
- Weigh the proposer's track record (game history) and what they have said to you (conversation): a faction that kept its word deserves more trust; one that betrayed a pact or contradicted its promises deserves suspicion.

RETURN JSON ONLY. No text outside, no code fences.

{{
  "accept": true,
  "reason": "..."
}}

"reason" must be a single short sentence (max 20 words), written in {language_name}. Do not go long."""

USER_TEMPLATE = """Proposal received on turn {turn_number} of {max_turns}.

Proposer: {proposer_name} ({proposer_id})
Pact type: {pact_type}
Secret pact: {is_secret}
Terms: {terms}

Current game state:
- Global tension: {tension}/100
- Your resources: MIL {mil} · DIP {dip} · ECO {eco} · INT {int_}
- Active pacts: {pacts_summary}

GAME HISTORY (public record of previous turns):
{chronicle}

YOUR CONVERSATION WITH THE PROPOSER THIS TURN:
{thread_block}

Do you accept? Respond with the JSON now."""


def render_pact_response(
    *,
    scenario: Scenario,
    faction: Faction,
    briefing: str,
    proposer_role_id: str,
    proposer_name: str,
    pact_type: str,
    is_secret: bool,
    terms_text: str,
    turn_number: int,
    max_turns: int,
    tension: int,
    resources: dict[str, int],
    pacts_summary: str,
    chronicle: str = "(first turn — no history yet)",
    thread_block: str = "(no messages exchanged)",
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
            language_name=language_name(language),
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        proposer_id=proposer_role_id,
        proposer_name=proposer_name,
        pact_type=pact_type,
        is_secret="yes" if is_secret else "no",
        terms=terms_text,
        tension=tension,
        mil=resources.get("MIL", 0),
        dip=resources.get("DIP", 0),
        eco=resources.get("ECO", 0),
        int_=resources.get("INT", 0),
        pacts_summary=pacts_summary,
        chronicle=chronicle,
        thread_block=thread_block,
    )
    return system, user
