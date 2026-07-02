"""AIService — composes prompts, dispatches to ClaudeClient, applies fallbacks.

Used by API routes (Phase 4) and bots (Phase 5). Tests mock ClaudeClient.
The service itself does not touch the DB; callers persist returned values.
"""

import logging
from dataclasses import dataclass

from anthropic import APIError

from src.ai.client import ClaudeClient, Models
from src.ai.parsing import (
    BotDecisionResponse,
    BotDiplomacyResponse,
    EvaluatedAction,
    EvaluationResponse,
    PactDecisionResponse,
    ParseError,
    parse_bot_decision,
    parse_bot_diplomacy,
    parse_evaluation_json,
    parse_pact_decision,
)
from src.ai.prompts.bot_decision import render_bot_decision
from src.ai.prompts.bot_diplomacy import render_bot_diplomacy
from src.ai.prompts.bot_message_reply import render_bot_message_reply
from src.ai.prompts.briefing import render_briefing
from src.ai.prompts.evaluation import render_evaluation
from src.ai.prompts.intel import render_intel
from src.ai.prompts.narrative import render_narrative
from src.ai.prompts.pact_response import render_pact_response
from src.schemas.scenario import Faction, Scenario

logger = logging.getLogger("crisis.ai.service")


def _fb(language: str, es: str, en: str) -> str:
    """Pick a fallback string in the game's language (defaults to Spanish)."""
    return en if language == "en" else es


@dataclass(frozen=True)
class TurnEvaluation:
    """Wraps the parsed evaluation plus a flag telling callers whether a
    fallback was used (useful for diagnostics)."""

    response: EvaluationResponse
    used_fallback: bool


class AIService:
    def __init__(self, client: ClaudeClient, haiku_only: bool = False):
        self.client = client
        self._haiku_only = haiku_only

    def _model(self, preferred: str) -> str:
        return Models.HAIKU if self._haiku_only else preferred

    # ----- Briefings -----

    async def generate_briefing(
        self, scenario: Scenario, faction: Faction, language: str = "es"
    ) -> str:
        system, user = render_briefing(scenario, faction, language)
        try:
            return await self.client.call(
                model=self._model(Models.SONNET),
                system=system,
                user_message=user,
                max_tokens=600,
                temperature=0.8,
            )
        except APIError as e:
            logger.warning("Briefing generation failed for %s: %s. Using fallback.", faction.id, e)
            return self._fallback_briefing(faction, language)

    def _fallback_briefing(self, faction: Faction, language: str = "es") -> str:
        res = faction.starting_resources
        if language == "en":
            return (
                f"## The Situation\n"
                f"You lead the delegation of {faction.name} ({faction.tagline}).\n\n"
                f"## Your Position\n{faction.description}\n\n"
                f"## What You Know\n"
                f"Your starting resources are: MIL {res.MIL}, DIP {res.DIP}, "
                f"ECO {res.ECO}, INT {res.INT}.\n\n"
                f"## What You Must Achieve\n{faction.public_objective.text}"
            )
        return (
            f"## La Situación\n"
            f"Estás al frente de la delegación de {faction.name} ({faction.tagline}).\n\n"
            f"## Tu Posición\n{faction.description}\n\n"
            f"## Lo que Sabes\n"
            f"Tus recursos iniciales son: MIL {res.MIL}, "
            f"DIP {res.DIP}, "
            f"ECO {res.ECO}, "
            f"INT {res.INT}.\n\n"
            f"## Lo que Debes Lograr\n{faction.public_objective.text}"
        )

    # ----- Evaluation (parses directives + scores) -----

    async def evaluate_turn(
        self,
        *,
        scenario: Scenario,
        turn_number: int,
        max_turns: int,
        tension_start: int,
        actions: list[dict],
        active_pacts: list[dict] | None = None,
        previous_events: str = "(none)",
        messages_block: str = "(none)",
    ) -> TurnEvaluation:
        system, user = render_evaluation(
            scenario=scenario,
            turn_number=turn_number,
            max_turns=max_turns,
            tension_start=tension_start,
            actions=actions,
            active_pacts=active_pacts,
            previous_events=previous_events,
            messages_block=messages_block,
        )
        try:
            raw = await self.client.call(
                model=self._model(Models.HAIKU),
                system=system,
                user_message=user,
                max_tokens=3000,
                temperature=0.3,
                prefill='{"evaluations":[',
            )
            parsed = parse_evaluation_json(raw)
            return TurnEvaluation(response=parsed, used_fallback=False)
        except (APIError, ParseError) as e:
            logger.warning(
                "Evaluation failed (turn %d): %s. Using deterministic fallback.",
                turn_number,
                e,
            )
            return TurnEvaluation(
                response=self._fallback_evaluation(actions), used_fallback=True
            )

    def _fallback_evaluation(self, actions: list[dict]) -> EvaluationResponse:
        return EvaluationResponse(
            evaluations=[
                EvaluatedAction(
                    player_id=a["player_id"],
                    action_type="generic",
                    target_id=None,
                    coherence_score=0.7,
                    posture_modifier=0.0,
                    decision_quality=5.0,
                    decision_quality_reasoning="(deterministic fallback)",
                    effective_multiplier=1.0,
                )
                for a in actions
            ]
        )

    # ----- Narrative -----

    async def generate_narrative(
        self,
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
    ) -> str:
        system, user = render_narrative(
            scenario=scenario,
            turn_number=turn_number,
            max_turns=max_turns,
            tension_start=tension_start,
            tension_end=tension_end,
            resolved_summary=resolved_summary,
            pacts_summary=pacts_summary,
            new_pacts=new_pacts,
            broken_pacts=broken_pacts,
            threshold_note=threshold_note,
            chronicle=chronicle,
            public_messages=public_messages,
            language=language,
        )
        try:
            return await self.client.call(
                model=self._model(Models.SONNET),
                system=system,
                user_message=user,
                max_tokens=450,
                temperature=0.8,
            )
        except APIError as e:
            logger.warning("Narrative failed (turn %d): %s. Using fallback.", turn_number, e)
            return _fb(
                language,
                f"El turno {turn_number} se resolvió. La tensión global pasó de "
                f"{tension_start} a {tension_end}.",
                f"Turn {turn_number} was resolved. Global tension moved from "
                f"{tension_start} to {tension_end}.",
            )

    # ----- Intel reports -----

    async def generate_intel(
        self,
        *,
        scenario: Scenario,
        turn_number: int,
        role_name: str,
        int_level: int,
        public_summary: str,
        own_action: str,
        private_observations: str = "(no new private data)",
        language: str = "es",
    ) -> str:
        system, user = render_intel(
            scenario=scenario,
            turn_number=turn_number,
            role_name=role_name,
            int_level=int_level,
            public_summary=public_summary,
            own_action=own_action,
            private_observations=private_observations,
            language=language,
        )
        try:
            return await self.client.call(
                model=self._model(Models.SONNET),
                system=system,
                user_message=user,
                max_tokens=150,
                temperature=0.7,
            )
        except APIError as e:
            logger.warning("Intel failed for %s turn %d: %s.", role_name, turn_number, e)
            return _fb(
                language,
                "Sin información nueva este turno.",
                "No new information this turn.",
            )


    # ----- Bot decisions -----

    async def decide_bot_action(
        self,
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
        credibility_block: str = "(unknown)",
        previous_intel: str = "(no previous report)",
        language: str = "es",
    ) -> BotDecisionResponse | None:
        """Returns a parsed BotDecisionResponse, or None on failure.

        Callers fall back to a stub decision when this returns None.
        """
        system, user = render_bot_decision(
            scenario=scenario,
            faction=faction,
            briefing=briefing,
            turn_number=turn_number,
            max_turns=max_turns,
            tension=tension,
            resources=resources,
            token_budget=token_budget,
            pacts_summary=pacts_summary,
            chronicle=chronicle,
            messages_block=messages_block,
            credibility_block=credibility_block,
            previous_intel=previous_intel,
            language=language,
        )
        try:
            raw = await self.client.call(
                model=self._model(Models.HAIKU),
                system=system,
                user_message=user,
                max_tokens=700,
                temperature=0.7,
                prefill='{"',
            )
            return parse_bot_decision(raw, expected_budget=token_budget)
        except (APIError, ParseError) as e:
            logger.warning(
                "Bot decision failed for %s on turn %d: %s.", faction.id, turn_number, e
            )
            return None


    # ----- Bot message replies (in-character diplomacy) -----

    async def reply_to_message(
        self,
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
    ) -> str | None:
        """In-character reply to a diplomatic message. Returns None on failure —
        an unanswered message is better than a canned non-answer.
        """
        system, user = render_bot_message_reply(
            scenario=scenario,
            faction=faction,
            briefing=briefing,
            sender_id=sender_id,
            sender_name=sender_name,
            incoming=incoming,
            turn_number=turn_number,
            max_turns=max_turns,
            tension=tension,
            pacts_summary=pacts_summary,
            chronicle=chronicle,
            thread_block=thread_block,
            language=language,
        )
        try:
            reply = await self.client.call(
                model=self._model(Models.HAIKU),
                system=system,
                user_message=user,
                max_tokens=200,
                temperature=0.8,
            )
        except APIError as e:
            logger.warning("Message reply failed for %s: %s.", faction.id, e)
            return None
        reply = reply.strip()
        return reply or None

    # ----- Bot diplomacy (optional move at turn start) -----

    async def decide_bot_diplomacy(
        self,
        *,
        scenario: Scenario,
        faction: Faction,
        briefing: str,
        turn_number: int,
        max_turns: int,
        tension: int,
        resources: dict[str, int],
        factions_list: str,
        pacts_summary: str = "(none)",
        chronicle: str = "(first turn — no history yet)",
        messages_block: str = "(none)",
        credibility_block: str = "(unknown)",
        previous_intel: str = "(no previous report)",
        language: str = "es",
    ) -> BotDiplomacyResponse | None:
        """One optional diplomatic move for a bot. Returns None on failure —
        callers simply skip the move (equivalent to action='none').
        """
        system, user = render_bot_diplomacy(
            scenario=scenario,
            faction=faction,
            briefing=briefing,
            turn_number=turn_number,
            max_turns=max_turns,
            tension=tension,
            resources=resources,
            factions_list=factions_list,
            pacts_summary=pacts_summary,
            chronicle=chronicle,
            messages_block=messages_block,
            credibility_block=credibility_block,
            previous_intel=previous_intel,
            language=language,
        )
        try:
            raw = await self.client.call(
                model=self._model(Models.HAIKU),
                system=system,
                user_message=user,
                max_tokens=400,
                temperature=0.7,
                prefill='{"',
            )
            return parse_bot_diplomacy(raw)
        except (APIError, ParseError) as e:
            logger.warning(
                "Bot diplomacy failed for %s on turn %d: %s.", faction.id, turn_number, e
            )
            return None

    # ----- Pact responses (bot accepts/rejects an incoming pact proposal) -----

    async def decide_pact_response(
        self,
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
        pacts_summary: str = "(none)",
        proposer_credibility: int = 50,
        chronicle: str = "(first turn — no history yet)",
        thread_block: str = "(no messages exchanged)",
        language: str = "es",
    ) -> PactDecisionResponse:
        """Returns a parsed decision. If Claude fails or parsing breaks, returns a
        heuristic default: reject for offensive-leaning roles, otherwise accept.
        """
        system, user = render_pact_response(
            scenario=scenario,
            faction=faction,
            briefing=briefing,
            proposer_role_id=proposer_role_id,
            proposer_name=proposer_name,
            pact_type=pact_type,
            is_secret=is_secret,
            terms_text=terms_text,
            turn_number=turn_number,
            max_turns=max_turns,
            tension=tension,
            resources=resources,
            pacts_summary=pacts_summary,
            proposer_credibility=proposer_credibility,
            chronicle=chronicle,
            thread_block=thread_block,
            language=language,
        )
        try:
            raw = await self.client.call(
                model=self._model(Models.HAIKU),
                system=system,
                user_message=user,
                max_tokens=400,
                temperature=0.4,
                prefill='{"',
            )
            return parse_pact_decision(raw)
        except (APIError, ParseError) as e:
            logger.warning(
                "Pact decision failed for %s (proposer %s, type %s): %s. "
                "Using heuristic default.",
                faction.id,
                proposer_role_id,
                pact_type,
                e,
            )
            # Heuristic fallback. Low-commitment pacts (non_aggression, intel_share)
            # are accepted by default. Higher-commitment ones (alliance, trade) are
            # accepted too once the game has progressed a bit and tension is
            # manageable — trust normally builds over a negotiation, so a blanket
            # rejection here would starve the whole pact system every time a
            # single Claude call fails to parse (which happens more than 0% of
            # the time in practice).
            low_commitment = pact_type in ("non_aggression", "intel_share")
            turn_progress = turn_number / max(1, max_turns)
            high_commitment_ok = tension < 70 and turn_progress >= 0.3
            return PactDecisionResponse(
                accept=low_commitment or high_commitment_ok,
                reason=_fb(language, "(fallback determinista)", "(deterministic fallback)"),
            )


__all__ = ["AIService", "TurnEvaluation"]
