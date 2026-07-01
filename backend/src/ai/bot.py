"""Bot decision logic.

`decide_stub` is the deterministic fallback used when Claude is unavailable or
returns an unparseable / invalid response. `decide_with_claude_or_fallback` is
the entry point the turn service uses: it asks the AIService to produce a
Claude-driven decision and falls through to the stub on failure.
"""

import random
from dataclasses import dataclass

from src.schemas.api import ActionSubmission, TokenAllocationDTO
from src.schemas.scenario import Faction, Scenario
from src.services.ai_service import AIService


@dataclass(frozen=True)
class BotDecision:
    submission: ActionSubmission
    source: str  # "claude" | "stub"
    reasoning: str = ""


def decide_stub(
    *, role_id: str, role_name: str, turn_number: int, token_budget: int
) -> BotDecision:
    """Distribute the budget pseudo-randomly but reproducibly per (role, turn)."""
    rng = random.Random(f"{role_id}-{turn_number}")
    domains = ["MIL", "DIP", "ECO", "INT"]
    allocation = {d: 0 for d in domains}
    for _ in range(token_budget):
        allocation[rng.choice(domains)] += 1

    posture = rng.choice(["ambiguous", "cooperative", "confrontational"])
    directive = (
        f"{role_name} mantiene su posición y observa el desarrollo del turno {turn_number}."
    )
    return BotDecision(
        submission=ActionSubmission(
            posture=posture,  # type: ignore[arg-type]
            tokens=TokenAllocationDTO(**allocation),
            directive=directive,
        ),
        source="stub",
    )


async def decide_with_claude_or_fallback(
    *,
    ai_service: AIService,
    scenario: Scenario,
    faction: Faction,
    briefing: str | None,
    turn_number: int,
    max_turns: int,
    tension: int,
    resources: dict[str, int],
    pacts_summary: str = "(ninguno)",
    previous_narrative: str = "(es el primer turno)",
    previous_intel: str = "(sin informe previo)",
) -> BotDecision:
    """Ask Claude for a decision. On failure (no briefing, API error, parse error,
    validation error), fall back to decide_stub.
    """
    token_budget = faction.token_budget_per_turn

    if not briefing:
        return decide_stub(
            role_id=faction.id,
            role_name=faction.name,
            turn_number=turn_number,
            token_budget=token_budget,
        )

    decision = await ai_service.decide_bot_action(
        scenario=scenario,
        faction=faction,
        briefing=briefing,
        turn_number=turn_number,
        max_turns=max_turns,
        tension=tension,
        resources=resources,
        token_budget=token_budget,
        pacts_summary=pacts_summary,
        previous_narrative=previous_narrative,
        previous_intel=previous_intel,
    )
    if decision is None:
        return decide_stub(
            role_id=faction.id,
            role_name=faction.name,
            turn_number=turn_number,
            token_budget=token_budget,
        )

    # ActionSubmission caps the directive at 300 chars; the bot-decision schema
    # allows up to 400 to give Claude some slack. Truncate rather than let
    # validation reject the whole decision and fall back to the generic stub.
    directive = decision.directive[:300]

    return BotDecision(
        submission=ActionSubmission(
            posture=decision.posture,  # type: ignore[arg-type]
            tokens=TokenAllocationDTO(
                MIL=decision.tokens.MIL,
                DIP=decision.tokens.DIP,
                ECO=decision.tokens.ECO,
                INT=decision.tokens.INT,
            ),
            directive=directive,
        ),
        source="claude",
        reasoning=decision.reasoning,
    )
