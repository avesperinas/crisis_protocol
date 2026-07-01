"""Pact endpoints: propose, break."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_ai_service, get_session
from src.schemas.api import (
    PactBreakResult,
    PactProposalResult,
    PactProposalSubmit,
)
from src.services.ai_service import AIService
from src.services.pact_service import PactServiceError, break_pact, propose_pact

router = APIRouter(prefix="/api/games", tags=["pacts"])


@router.post("/{game_id}/pacts/propose", response_model=PactProposalResult)
async def propose(
    game_id: str,
    role_id: str,
    payload: PactProposalSubmit,
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
) -> PactProposalResult:
    try:
        result = await propose_pact(
            session,
            ai_service=ai_service,
            game_id=game_id,
            proposer_role_id=role_id,
            target_role_id=payload.target_role_id,
            pact_type=payload.pact_type,
            is_secret=payload.is_secret,
        )
    except PactServiceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return PactProposalResult(
        accepted=result.accepted,
        pact_id=result.pact_id,
        proposal_message_id=result.proposal_message_id,
        reason=result.reason,
    )


@router.post("/{game_id}/pacts/{pact_id}/break", response_model=PactBreakResult)
async def break_existing(
    game_id: str,
    pact_id: str,
    role_id: str,
    session: AsyncSession = Depends(get_session),
) -> PactBreakResult:
    try:
        pact = await break_pact(
            session, game_id=game_id, breaker_role_id=role_id, pact_id=pact_id
        )
    except PactServiceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    # Fetch updated game tension + breaker DIP for the response.
    from sqlalchemy import select

    from src.models import Game, Player

    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one()
    breaker = (
        await session.execute(
            select(Player).where(Player.game_id == game_id, Player.role_id == role_id)
        )
    ).scalar_one()
    return PactBreakResult(
        pact_id=pact.id,
        new_tension=game.tension,
        breaker_dip_after=breaker.resources.get("DIP", 0),
    )
