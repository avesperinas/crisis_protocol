"""Message endpoints: send (public or bilateral). Listing happens through the
state endpoint (which already filters by visibility)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.schemas.api import MessageSubmit
from src.services.message_service import MessageServiceError, send_message

router = APIRouter(prefix="/api/games", tags=["messages"])


@router.post("/{game_id}/messages")
async def send(
    game_id: str,
    role_id: str,
    payload: MessageSubmit,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        msg = await send_message(
            session,
            game_id=game_id,
            from_role_id=role_id,
            to_role_id=payload.to_role_id,
            content=payload.content,
        )
    except MessageServiceError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return {"message_id": msg.id}
