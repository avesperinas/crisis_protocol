"""Robust JSON parsing for Claude evaluation responses.

Claude sometimes wraps JSON in markdown code fences or prepends a short
sentence. This module strips those, parses, and validates against a Pydantic
schema. On failure it raises ParseError; callers can decide to fallback.
"""

import json
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.engine.types import ActionType


def _clamp(lo: float, hi: float):
    """Clamp out-of-range numeric scores instead of rejecting the whole response —
    Claude occasionally returns e.g. decision_quality=10.4 or coherence_score=1.02,
    a cosmetic overshoot that shouldn't nuke an otherwise-valid evaluation."""

    def validator(v: float) -> float:
        try:
            v = float(v)
        except (TypeError, ValueError):
            return v
        return max(lo, min(hi, v))

    return validator


class EvaluatedAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    player_id: str
    action_type: str = "generic"
    target_id: str | None = None
    coherence_score: float = Field(ge=0.0, le=1.0)
    posture_modifier: float = Field(ge=-0.25, le=0.20, default=0.0)
    decision_quality: float = Field(ge=0.0, le=10.0)
    decision_quality_reasoning: str = ""
    effective_multiplier: float = Field(ge=0.3, le=1.2, default=1.0)

    _clamp_coherence = field_validator("coherence_score", mode="before")(_clamp(0.0, 1.0))
    _clamp_posture = field_validator("posture_modifier", mode="before")(_clamp(-0.25, 0.20))
    _clamp_dq = field_validator("decision_quality", mode="before")(_clamp(0.0, 10.0))
    _clamp_mult = field_validator("effective_multiplier", mode="before")(_clamp(0.3, 1.2))

    def action_type_enum(self) -> ActionType:
        try:
            return ActionType(self.action_type)
        except ValueError:
            return ActionType.GENERIC


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evaluations: list[EvaluatedAction]


class ParseError(ValueError):
    pass


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1)
    return text


def _extract_first_json_object(text: str) -> str | None:
    """Find the first balanced {...} block in text and return it."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_evaluation_json(text: str) -> EvaluationResponse:
    """Parse and validate Claude's evaluation response.

    Order of attempts:
      1. Strip markdown fences.
      2. json.loads directly.
      3. Extract the first balanced object and try again.
      4. Raise ParseError.
    """
    stripped = _strip_fences(text.strip())

    candidates: list[str] = [stripped]
    extracted = _extract_first_json_object(stripped)
    if extracted and extracted != stripped:
        candidates.append(extracted)

    last_err: Exception | None = None
    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        try:
            return EvaluationResponse.model_validate(data)
        except ValidationError as e:
            last_err = e
            continue

    raise ParseError(f"Could not parse evaluation response: {last_err}")


class PactDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accept: bool
    reason: str = ""


def parse_pact_decision(text: str) -> PactDecisionResponse:
    stripped = _strip_fences(text.strip())
    candidates: list[str] = [stripped]
    extracted = _extract_first_json_object(stripped)
    if extracted and extracted != stripped:
        candidates.append(extracted)
    last_err: Exception | None = None
    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        try:
            return PactDecisionResponse.model_validate(data)
        except ValidationError as e:
            last_err = e
            continue
    raise ParseError(f"Could not parse pact decision: {last_err}")


class BotTokens(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Claude sometimes omits a domain entirely when it allocates 0 to it —
    # treat a missing field as 0 instead of rejecting the whole response.
    MIL: int = Field(ge=0, default=0)
    DIP: int = Field(ge=0, default=0)
    ECO: int = Field(ge=0, default=0)
    INT: int = Field(ge=0, default=0)

    def total(self) -> int:
        return self.MIL + self.DIP + self.ECO + self.INT


class BotDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    posture: str
    tokens: BotTokens
    directive: str = Field(min_length=1, max_length=400)
    reasoning: str = ""


def parse_bot_decision(text: str, expected_budget: int) -> BotDecisionResponse:
    """Parse and validate a bot decision JSON. Raises ParseError if invalid or
    budget mismatch. Same fence/balanced-object handling as parse_evaluation_json.
    """
    stripped = _strip_fences(text.strip())
    candidates: list[str] = [stripped]
    extracted = _extract_first_json_object(stripped)
    if extracted and extracted != stripped:
        candidates.append(extracted)

    last_err: Exception | None = None
    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        try:
            decision = BotDecisionResponse.model_validate(data)
        except ValidationError as e:
            last_err = e
            continue
        if decision.posture not in ("confrontational", "cooperative", "ambiguous"):
            last_err = ValueError(f"invalid posture: {decision.posture!r}")
            continue
        if decision.tokens.total() != expected_budget:
            last_err = ValueError(
                f"token sum {decision.tokens.total()} does not match budget {expected_budget}"
            )
            continue
        return decision

    raise ParseError(f"Could not parse bot decision: {last_err}")


class BotDiplomacyResponse(BaseModel):
    """A bot's optional diplomatic move at the start of a turn."""

    model_config = ConfigDict(extra="ignore")

    action: str  # none | message_public | message_private | propose_pact
    target_id: str | None = None
    content: str = Field(default="", max_length=600)
    pact_type: str | None = None
    is_secret: bool = False
    reasoning: str = ""


_DIPLOMACY_ACTIONS = ("none", "message_public", "message_private", "propose_pact")
_DIPLOMACY_PACT_TYPES = ("alliance", "non_aggression", "trade", "intel_share")


def parse_bot_diplomacy(text: str) -> BotDiplomacyResponse:
    """Parse and validate a bot diplomacy JSON. Raises ParseError if the shape
    is invalid or the action's required fields are missing.
    """
    stripped = _strip_fences(text.strip())
    candidates: list[str] = [stripped]
    extracted = _extract_first_json_object(stripped)
    if extracted and extracted != stripped:
        candidates.append(extracted)

    last_err: Exception | None = None
    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        try:
            decision = BotDiplomacyResponse.model_validate(data)
        except ValidationError as e:
            last_err = e
            continue
        if decision.action not in _DIPLOMACY_ACTIONS:
            last_err = ValueError(f"invalid diplomacy action: {decision.action!r}")
            continue
        if decision.action in ("message_public", "message_private") and not decision.content.strip():
            last_err = ValueError("message action requires non-empty content")
            continue
        if decision.action in ("message_private", "propose_pact") and not decision.target_id:
            last_err = ValueError(f"{decision.action} requires target_id")
            continue
        if decision.action == "propose_pact" and decision.pact_type not in _DIPLOMACY_PACT_TYPES:
            last_err = ValueError(f"invalid pact_type: {decision.pact_type!r}")
            continue
        return decision

    raise ParseError(f"Could not parse bot diplomacy: {last_err}")


__all__ = [
    "BotDecisionResponse",
    "BotDiplomacyResponse",
    "BotTokens",
    "EvaluatedAction",
    "EvaluationResponse",
    "PactDecisionResponse",
    "ParseError",
    "parse_bot_decision",
    "parse_bot_diplomacy",
    "parse_evaluation_json",
    "parse_pact_decision",
]
