"""Turn action submission."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_ai_service, get_session
from src.schemas.api import ActionSubmission, ActionSubmittedResponse
from src.services.ai_service import AIService
from src.services.turn_service import TurnServiceError, submit_human_action

router = APIRouter(prefix="/api/games", tags=["turns"])


@router.post("/{game_id}/actions", response_model=ActionSubmittedResponse)
async def submit_action(
    game_id: str,
    role_id: str,
    payload: ActionSubmission,
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
) -> ActionSubmittedResponse:
    try:
        resolved, message = await submit_human_action(
            session,
            ai_service=ai_service,
            game_id=game_id,
            role_id=role_id,
            submission=payload,
        )
    except TurnServiceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return ActionSubmittedResponse(accepted=True, turn_resolved=resolved, message=message)
